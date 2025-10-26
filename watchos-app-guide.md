# Haven watchOS App - Implementation Guide

This guide contains all the code needed to build the Haven watchOS app for collecting patient vitals.

## Project Setup

1. Open Xcode
2. Create New Project → watchOS → App
3. Product Name: "HavenWatch"
4. Interface: SwiftUI
5. Include Unit Tests: No

## Required Capabilities

In Xcode, enable these capabilities in your watch target:

1. **HealthKit** - Required for accessing vitals
   - Signing & Capabilities → + Capability → HealthKit

2. **Background Modes** - For background health data collection
   - Signing & Capabilities → + Capability → Background Modes
   - Enable: "Health" checkbox

## Info.plist Configuration

Add these keys to your `Info.plist`:

```xml
<key>NSHealthShareUsageDescription</key>
<string>Haven needs access to your health data to monitor your vitals for clinical care.</string>

<key>NSHealthUpdateUsageDescription</key>
<string>Haven may write health data for record keeping.</string>

<key>WKBackgroundModes</key>
<array>
    <string>workout-processing</string>
    <string>health</string>
</array>
```

## Project Structure

```
HavenWatch/
├── App/
│   └── HavenWatchApp.swift
├── Views/
│   ├── ContentView.swift
│   ├── PairingView.swift
│   └── Components/
│       └── VitalBadge.swift
├── Services/
│   ├── HealthKitManager.swift
│   ├── WebSocketService.swift
│   └── PairingService.swift
├── Models/
│   ├── Vitals.swift
│   └── DeviceInfo.swift
└── Assets.xcassets/
```

---

## Complete Source Code

### 1. HavenWatchApp.swift

```swift
import SwiftUI

@main
struct HavenWatchApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

### 2. Models/Vitals.swift

```swift
import Foundation

struct WearableVitals: Codable {
    let deviceId: String
    let patientId: String
    let timestamp: String
    let heartRate: Int?
    let heartRateVariability: Double?
    let spo2: Int?
    let respiratoryRate: Int?
    let bodyTemperature: Double?
    let confidence: Double?
    let batteryLevel: Int?
    let isActive: Bool

    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case patientId = "patient_id"
        case timestamp
        case heartRate = "heart_rate"
        case heartRateVariability = "heart_rate_variability"
        case spo2
        case respiratoryRate = "respiratory_rate"
        case bodyTemperature = "body_temperature"
        case confidence
        case batteryLevel = "battery_level"
        case isActive = "is_active"
    }
}
```

### 3. Models/DeviceInfo.swift

```swift
import Foundation
import WatchKit

struct DeviceInfo: Codable {
    let deviceType: String = "apple_watch"
    let model: String
    let osVersion: String
    let deviceName: String

    enum CodingKeys: String, CodingKey {
        case deviceType = "device_type"
        case model
        case osVersion = "os_version"
        case deviceName = "device_name"
    }

    static func current() -> DeviceInfo {
        let device = WKInterfaceDevice.current()
        return DeviceInfo(
            model: device.model,
            osVersion: device.systemVersion,
            deviceName: device.name
        )
    }
}

enum PairingError: Error {
    case invalidCode
    case invalidResponse
    case networkError
}
```

### 4. Services/HealthKitManager.swift

```swift
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
```

### 5. Services/PairingService.swift

```swift
import Foundation

class PairingService {
    static let baseURL = "https://api-haven.onrender.com"  // Update with your API URL

    static func completePairing(code: String, deviceInfo: DeviceInfo) async throws -> String {
        let url = URL(string: "\(baseURL)/wearable/pair/complete")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "pairing_code": code,
            "device_info": [
                "device_type": deviceInfo.deviceType,
                "model": deviceInfo.model,
                "os_version": deviceInfo.osVersion,
                "device_name": deviceInfo.deviceName
            ]
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw PairingError.invalidCode
        }

        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let deviceId = json?["device_id"] as? String else {
            throw PairingError.invalidResponse
        }

        return deviceId
    }
}
```

### 6. Services/WebSocketService.swift

```swift
import Foundation
import Combine

class WebSocketService: ObservableObject {
    @Published var isConnected = false
    @Published var connectionError: String?

    private var webSocketTask: URLSessionWebSocketTask?
    private let deviceId: String
    private let baseURL = "wss://api-haven.onrender.com/ws/wearable"  // Update with your API URL

    init(deviceId: String) {
        self.deviceId = deviceId
    }

    func connect() {
        let urlString = "\(baseURL)/\(deviceId)"
        guard let url = URL(string: urlString) else {
            connectionError = "Invalid URL"
            return
        }

        webSocketTask = URLSession.shared.webSocketTask(with: url)
        webSocketTask?.resume()

        isConnected = true
        receiveMessage() // Start listening

        // Send ping every 30 seconds
        startPingTimer()
    }

    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        isConnected = false
    }

    func sendVitals(_ vitals: WearableVitals) {
        guard let data = try? JSONEncoder().encode(vitals) else { return }

        let message: [String: Any] = [
            "type": "vitals",
            "vitals": try? JSONSerialization.jsonObject(with: data)
        ]

        guard let jsonData = try? JSONSerialization.data(withJSONObject: message) else { return }
        let wsMessage = URLSessionWebSocketTask.Message.data(jsonData)

        webSocketTask?.send(wsMessage) { error in
            if let error = error {
                print("WebSocket send error: \(error)")
            }
        }
    }

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                // Handle incoming messages (e.g., ack, pong)
                print("Received message: \(message)")
                self?.receiveMessage() // Continue listening
            case .failure(let error):
                print("WebSocket receive error: \(error)")
                self?.isConnected = false
            }
        }
    }

    private func startPingTimer() {
        Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            guard let self = self, self.isConnected else { return }

            let pingMessage: [String: String] = ["type": "ping"]
            if let data = try? JSONSerialization.data(withJSONObject: pingMessage) {
                let message = URLSessionWebSocketTask.Message.data(data)
                self.webSocketTask?.send(message) { _ in }
            }
        }
    }
}
```

### 7. Views/Components/VitalBadge.swift

```swift
import SwiftUI

struct VitalBadge: View {
    let icon: String
    let value: String
    let label: String

    var body: some View {
        VStack(spacing: 2) {
            Image(systemName: icon)
                .font(.caption)
            Text(value)
                .font(.system(.body, design: .monospaced))
                .fontWeight(.medium)
            Text(label)
                .font(.caption2)
                .foregroundColor(.gray)
        }
    }
}
```

### 8. Views/PairingView.swift

```swift
import SwiftUI

struct PairingView: View {
    @State private var pairingCode = ""
    @State private var isLoading = false
    @State private var errorMessage = ""

    let onPaired: (String) -> Void

    var body: some View {
        VStack(spacing: 12) {
            Text("Enter Pairing Code")
                .font(.headline)

            TextField("6-digit code", text: $pairingCode)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.numberPad)
                .frame(maxWidth: 120)
                .multilineTextAlignment(.center)
                .font(.system(.title2, design: .monospaced))

            if !errorMessage.isEmpty {
                Text(errorMessage)
                    .font(.caption2)
                    .foregroundColor(.red)
            }

            Button(action: submitPairingCode) {
                if isLoading {
                    ProgressView()
                } else {
                    Text("Pair")
                }
            }
            .disabled(pairingCode.count != 6 || isLoading)
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }

    private func submitPairingCode() {
        isLoading = true
        errorMessage = ""

        Task {
            do {
                let deviceId = try await PairingService.completePairing(
                    code: pairingCode,
                    deviceInfo: DeviceInfo.current()
                )
                await MainActor.run {
                    onPaired(deviceId)
                }
            } catch {
                await MainActor.run {
                    errorMessage = "Invalid code"
                    isLoading = false
                }
            }
        }
    }
}
```

### 9. Views/ContentView.swift

```swift
import SwiftUI
import WatchKit

struct ContentView: View {
    @StateObject private var healthKit = HealthKitManager()
    @StateObject private var webSocket: WebSocketService

    @State private var isPaired = false
    @AppStorage("deviceId") private var deviceId = ""
    @AppStorage("patientId") private var patientId = ""

    init() {
        let savedDeviceId = UserDefaults.standard.string(forKey: "deviceId") ?? ""
        _webSocket = StateObject(wrappedValue: WebSocketService(deviceId: savedDeviceId))
    }

    var body: some View {
        if isPaired && !deviceId.isEmpty {
            // Monitoring Dashboard
            VStack(spacing: 8) {
                // Status indicator
                HStack {
                    Circle()
                        .fill(webSocket.isConnected ? Color.green : Color.red)
                        .frame(width: 8, height: 8)
                    Text("Haven")
                        .font(.caption)
                }

                // Heart Rate (large and prominent)
                VStack {
                    Text("\(healthKit.heartRate)")
                        .font(.system(size: 48, weight: .bold, design: .rounded))
                        .foregroundColor(healthKit.heartRate > 0 ? .primary : .gray)
                    Text("BPM")
                        .font(.caption2)
                        .foregroundColor(.gray)
                }

                // Other vitals (compact)
                HStack(spacing: 12) {
                    VitalBadge(
                        icon: "waveform.path.ecg",
                        value: "\(Int(healthKit.hrv))",
                        label: "HRV"
                    )
                    VitalBadge(
                        icon: "lungs.fill",
                        value: "\(healthKit.spo2)",
                        label: "SpO₂"
                    )
                }
                .font(.caption2)

                // Battery indicator
                Text("Battery: \(batteryLevel())%")
                    .font(.caption2)
                    .foregroundColor(.gray)
            }
            .padding()
            .onAppear {
                startMonitoring()
            }
        } else {
            // Pairing View
            PairingView(onPaired: { newDeviceId in
                self.deviceId = newDeviceId
                self.isPaired = true
                // Reinitialize WebSocket with new device ID
                webSocket.connect()
            })
        }
    }

    private func startMonitoring() {
        Task {
            try? await healthKit.requestAuthorization()
            healthKit.startHeartRateStream()

            // Connect WebSocket
            webSocket.connect()

            // Periodic vitals updates (every 10 seconds)
            Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { _ in
                Task {
                    await sendVitalsUpdate()
                }
            }
        }
    }

    private func sendVitalsUpdate() async {
        let hrv = await healthKit.fetchHRV()
        let spo2 = await healthKit.fetchSpO2()
        let rr = await healthKit.fetchRespiratoryRate()

        let vitals = WearableVitals(
            deviceId: deviceId,
            patientId: patientId,
            timestamp: ISO8601DateFormatter().string(from: Date()),
            heartRate: healthKit.heartRate > 0 ? healthKit.heartRate : nil,
            heartRateVariability: hrv,
            spo2: spo2,
            respiratoryRate: rr,
            bodyTemperature: nil,
            confidence: 1.0,
            batteryLevel: batteryLevel(),
            isActive: true
        )

        webSocket.sendVitals(vitals)
    }

    private func batteryLevel() -> Int {
        let level = WKInterfaceDevice.current().batteryLevel
        return level >= 0 ? Int(level * 100) : 100
    }
}
```

---

## Building & Testing

1. **Set Development Team**: Signing & Capabilities → Team
2. **Build**: Cmd+B
3. **Run on Simulator**: Cmd+R (select watchOS Simulator)
4. **Run on Physical Watch**:
   - Connect iPhone to Mac
   - Ensure watch is paired and unlocked
   - Select your watch from device list
   - Cmd+R

## Testing Checklist

- [ ] HealthKit authorization prompt appears
- [ ] Pairing code entry works
- [ ] Backend receives pairing request
- [ ] WebSocket connects successfully
- [ ] Heart rate updates in real-time
- [ ] Vitals sent every 10 seconds
- [ ] Dashboard receives vitals
- [ ] Battery level displays correctly
- [ ] App reconnects after backgrounding

## Troubleshooting

**HealthKit not working:**
- Check Info.plist has NSHealthShareUsageDescription
- Check HealthKit capability is enabled
- Ensure device/simulator supports HealthKit

**WebSocket connection fails:**
- Check API URL is correct (wss:// not ws://)
- Verify device_id is stored correctly
- Check backend is running and accessible

**No heart rate data:**
- Start a Workout on watch to trigger sensors
- Check HealthKit authorization was granted
- May take 30-60 seconds for first reading

## Next Steps

Once watchOS app is built and tested, return to the main implementation guide to continue with frontend components.
