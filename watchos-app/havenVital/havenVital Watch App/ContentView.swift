//
//  ContentView.swift
//  havenVital Watch App
//
//  Created by David Jr on 10/25/25.
//

import SwiftUI
import WatchKit

struct ContentView: View {
    @StateObject private var healthKit = HealthKitManager()
    @State private var webSocket: WebSocketService?

    @State private var isPaired = false
    @AppStorage("deviceId") private var deviceId = ""
    @AppStorage("patientId") private var patientId = ""

    var body: some View {
        if isPaired && !deviceId.isEmpty {
            // Monitoring Dashboard
            VStack(spacing: 8) {
                // Status indicator
                HStack {
                    Circle()
                        .fill((webSocket?.isConnected ?? false) ? Color.green : Color.red)
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
            PairingView(onPaired: { newDeviceId, newPatientId in
                self.deviceId = newDeviceId
                self.patientId = newPatientId
                self.isPaired = true

                // Initialize WebSocket with new device ID
                self.webSocket = WebSocketService(deviceId: newDeviceId)
                self.webSocket?.connect()
            })
        }
    }

    private func startMonitoring() {
        Task {
            try? await healthKit.requestAuthorization()
            healthKit.startHeartRateStream()

            // Initialize and connect WebSocket
            if webSocket == nil {
                webSocket = WebSocketService(deviceId: deviceId)
            }
            webSocket?.connect()

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

        webSocket?.sendVitals(vitals)
    }

    private func batteryLevel() -> Int {
        let level = WKInterfaceDevice.current().batteryLevel
        return level >= 0 ? Int(level * 100) : 100
    }
}

#Preview {
    ContentView()
}
