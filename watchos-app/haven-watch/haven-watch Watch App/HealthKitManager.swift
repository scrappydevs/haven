import Foundation
import HealthKit

class HealthKitManager: ObservableObject {
    let healthStore = HKHealthStore()
    private var timer: Timer?
    private var currentPatientId: String?

    // Backend configuration
    private let backendURL = "https://your-backend-url.com" // CHANGE THIS to your backend URL
    // For local testing: "http://YOUR-COMPUTER-IP:8000"

    // Published properties for UI updates
    @Published var latestHeartRate: Double?
    @Published var latestRespiratoryRate: Double?
    @Published var latestSpO2: Double?
    @Published var latestTemperature: Double?
    @Published var latestHRV: Double?

    // HealthKit queries
    private var heartRateQuery: HKAnchoredObjectQuery?
    private var respiratoryQuery: HKAnchoredObjectQuery?

    // Request HealthKit permissions
    func requestAuthorization() {
        guard HKHealthStore.isHealthDataAvailable() else {
            print("❌ HealthKit not available")
            return
        }

        let typesToRead: Set<HKObjectType> = [
            HKQuantityType(.heartRate),
            HKQuantityType(.respiratoryRate),
            HKQuantityType(.oxygenSaturation),
            HKQuantityType(.bodyTemperature),
            HKQuantityType(.heartRateVariabilitySDNN)
        ]

        healthStore.requestAuthorization(toShare: [], read: typesToRead) { success, error in
            if success {
                print("✅ HealthKit authorized")
            } else {
                print("❌ HealthKit authorization failed: \(error?.localizedDescription ?? "unknown")")
            }
        }
    }

    // Start monitoring and streaming data
    func startMonitoring(patientId: String, completion: @escaping (Bool) -> Void) {
        currentPatientId = patientId
        print("⌚ Starting monitoring for patient \(patientId)")

        // Start real-time queries for heart rate
        startHeartRateStreaming()

        // Start timer to batch send data every 4 seconds
        timer = Timer.scheduledTimer(withTimeInterval: 4.0, repeats: true) { [weak self] _ in
            self?.fetchAndSendMetrics()
        }

        // Fetch initial metrics immediately
        fetchAndSendMetrics()

        completion(true)
    }

    // Stop monitoring
    func stopMonitoring() {
        timer?.invalidate()
        timer = nil
        currentPatientId = nil

        if let query = heartRateQuery {
            healthStore.stop(query)
        }

        print("⌚ Monitoring stopped")
    }

    // Start real-time heart rate streaming
    private func startHeartRateStreaming() {
        let heartRateType = HKQuantityType(.heartRate)

        let query = HKAnchoredObjectQuery(
            type: heartRateType,
            predicate: nil,
            anchor: nil,
            limit: HKObjectQueryNoLimit
        ) { [weak self] query, samples, deletedObjects, anchor, error in
            self?.processHeartRateSamples(samples)
        }

        query.updateHandler = { [weak self] query, samples, deletedObjects, anchor, error in
            self?.processHeartRateSamples(samples)
        }

        healthStore.execute(query)
        heartRateQuery = query
        print("✅ Heart rate streaming started")
    }

    private func processHeartRateSamples(_ samples: [HKSample]?) {
        guard let quantitySamples = samples as? [HKQuantitySample] else { return }

        for sample in quantitySamples {
            let bpm = sample.quantity.doubleValue(for: HKUnit.count().unitDivided(by: .minute()))
            DispatchQueue.main.async {
                self.latestHeartRate = bpm
            }
        }
    }

    // Fetch all metrics and send to backend
    private func fetchAndSendMetrics() {
        guard let patientId = currentPatientId else { return }

        // Fetch latest samples for each metric type
        let group = DispatchGroup()

        // Heart Rate
        group.enter()
        fetchLatestQuantity(for: .heartRate, unit: HKUnit.count().unitDivided(by: .minute())) { value in
            self.latestHeartRate = value
            group.leave()
        }

        // Respiratory Rate
        group.enter()
        fetchLatestQuantity(for: .respiratoryRate, unit: HKUnit.count().unitDivided(by: .minute())) { value in
            self.latestRespiratoryRate = value
            group.leave()
        }

        // SpO2
        group.enter()
        fetchLatestQuantity(for: .oxygenSaturation, unit: HKUnit.percent()) { value in
            // Convert from 0-1 to 0-100
            self.latestSpO2 = value != nil ? value! * 100 : nil
            group.leave()
        }

        // Temperature (may not be available on all devices)
        group.enter()
        fetchLatestQuantity(for: .bodyTemperature, unit: HKUnit.degreeCelsius()) { value in
            self.latestTemperature = value
            group.leave()
        }

        // HRV
        group.enter()
        fetchLatestQuantity(for: .heartRateVariabilitySDNN, unit: HKUnit.secondUnit(with: .milli)) { value in
            self.latestHRV = value
            group.leave()
        }

        // When all fetches complete, send to backend
        group.notify(queue: .main) {
            self.sendMetricsToBackend(patientId: patientId)
        }
    }

    private func fetchLatestQuantity(for identifier: HKQuantityTypeIdentifier, unit: HKUnit, completion: @escaping (Double?) -> Void) {
        let quantityType = HKQuantityType(identifier)
        let sortDescriptor = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)

        let query = HKSampleQuery(
            sampleType: quantityType,
            predicate: nil,
            limit: 1,
            sortDescriptors: [sortDescriptor]
        ) { query, samples, error in
            guard let sample = samples?.first as? HKQuantitySample else {
                completion(nil)
                return
            }

            let value = sample.quantity.doubleValue(for: unit)
            completion(value)
        }

        healthStore.execute(query)
    }

    // Send metrics to Haven backend
    private func sendMetricsToBackend(patientId: String) {
        guard let url = URL(string: "\(backendURL)/watch-metrics/\(patientId)") else {
            print("❌ Invalid backend URL")
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = [
            "patient_id": patientId,
            "timestamp": ISO8601DateFormatter().string(from: Date()),
            "heart_rate": latestHeartRate as Any,
            "respiratory_rate": latestRespiratoryRate as Any,
            "spo2": latestSpO2 as Any,
            "temperature": latestTemperature as Any,
            "hrv": latestHRV as Any,
            "step_count": nil as Any,
            "active_calories": nil as Any,
            "fall_detected": false
        ]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        } catch {
            print("❌ Failed to serialize payload: \(error)")
            return
        }

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("❌ Network error: \(error.localizedDescription)")
                return
            }

            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 200 {
                    print("✅ Metrics sent for \(patientId) - HR: \(self.latestHeartRate ?? 0), RR: \(self.latestRespiratoryRate ?? 0)")
                } else {
                    print("⚠️ Server returned status \(httpResponse.statusCode)")
                }
            }
        }.resume()
    }
}
