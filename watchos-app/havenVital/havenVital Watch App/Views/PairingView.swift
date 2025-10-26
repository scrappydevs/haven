import SwiftUI

struct PairingView: View {
    @State private var pairingCode = ""
    @State private var isLoading = false
    @State private var errorMessage = ""

    let onPaired: (String, String) -> Void  // (deviceId, patientId)

    var body: some View {
        ScrollView {
            VStack(spacing: 8) {
                Text("Enter Code")
                    .font(.headline)

                TextField("6-digit", text: $pairingCode)
                    .font(.system(size: 24, weight: .bold, design: .monospaced))
                    .multilineTextAlignment(.center)
                    .frame(height: 40)

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
    }

    private func submitPairingCode() {
        isLoading = true
        errorMessage = ""

        Task {
            do {
                let (deviceId, patientId) = try await PairingService.completePairing(
                    code: pairingCode,
                    deviceInfo: DeviceInfo.current()
                )
                await MainActor.run {
                    onPaired(deviceId, patientId)
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
