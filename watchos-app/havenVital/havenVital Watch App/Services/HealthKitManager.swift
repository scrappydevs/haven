import HealthKit
import Combine

class HealthKitManager: ObservableObject {
    private let healthStore = HKHealthStore()

    @Published var heartRate: Int = 0
    @Published var hrv: Double = 0
    @Published var spo2: Int = 0
    @Published var respiratoryRate: Int = 0

    private var heartRateQuery: HKAnchoredObjectQuery?

    // Request HealthKit authorization
    func requestAuthorization() async throws {
        let types: Set<HKSampleType> = [
            HKQuantityType(.heartRate),
            HKQuantityType(.heartRateVariabilitySDNN),
            HKQuantityType(.oxygenSaturation),
            HKQuantityType(.respiratoryRate),
        ]

        try await healthStore.requestAuthorization(toShare: [], read: types)
    }

    // Start continuous heart rate monitoring
    func startHeartRateStream() {
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
    }

    func stopHeartRateStream() {
        if let query = heartRateQuery {
            healthStore.stop(query)
            heartRateQuery = nil
        }
    }

    private func processHeartRateSamples(_ samples: [HKSample]?) {
        guard let samples = samples as? [HKQuantitySample] else { return }
        guard let latest = samples.last else { return }

        let hr = Int(latest.quantity.doubleValue(for: HKUnit(from: "count/min")))
        DispatchQueue.main.async {
            self.heartRate = hr
        }
    }

    // Fetch HRV (every 5 minutes)
    func fetchHRV() async -> Double? {
        let hrvType = HKQuantityType(.heartRateVariabilitySDNN)
        let now = Date()
        let fiveMinutesAgo = now.addingTimeInterval(-300)

        let predicate = HKQuery.predicateForSamples(
            withStart: fiveMinutesAgo,
            end: now
        )

        return await withCheckedContinuation { continuation in
            let query = HKStatisticsQuery(
                quantityType: hrvType,
                quantitySamplePredicate: predicate,
                options: .discreteAverage
            ) { _, statistics, _ in
                let hrv = statistics?.averageQuantity()?.doubleValue(for: HKUnit.secondUnit(with: .milli))
                continuation.resume(returning: hrv)
            }
            healthStore.execute(query)
        }
    }

    // Fetch SpO2 (every 2 minutes)
    func fetchSpO2() async -> Int? {
        let spo2Type = HKQuantityType(.oxygenSaturation)
        let now = Date()
        let twoMinutesAgo = now.addingTimeInterval(-120)

        let predicate = HKQuery.predicateForSamples(
            withStart: twoMinutesAgo,
            end: now
        )

        return await withCheckedContinuation { continuation in
            let query = HKSampleQuery(
                sampleType: spo2Type,
                predicate: predicate,
                limit: 1,
                sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)]
            ) { _, samples, _ in
                guard let sample = samples?.first as? HKQuantitySample else {
                    continuation.resume(returning: nil)
                    return
                }
                let spo2 = Int(sample.quantity.doubleValue(for: HKUnit.percent()) * 100)
                continuation.resume(returning: spo2)
            }
            healthStore.execute(query)
        }
    }

    // Fetch respiratory rate (every 5 minutes)
    func fetchRespiratoryRate() async -> Int? {
        let rrType = HKQuantityType(.respiratoryRate)
        let now = Date()
        let fiveMinutesAgo = now.addingTimeInterval(-300)

        let predicate = HKQuery.predicateForSamples(
            withStart: fiveMinutesAgo,
            end: now
        )

        return await withCheckedContinuation { continuation in
            let query = HKStatisticsQuery(
                quantityType: rrType,
                quantitySamplePredicate: predicate,
                options: .discreteAverage
            ) { _, statistics, _ in
                let rr = statistics?.averageQuantity()?.doubleValue(for: HKUnit(from: "count/min"))
                continuation.resume(returning: rr.map { Int($0) })
            }
            healthStore.execute(query)
        }
    }
}
