import Foundation

class PairingService {
    static let baseURL = "https://api-haven.onrender.com"  // Update with your backend URL

    static func completePairing(code: String, deviceInfo: DeviceInfo) async throws -> (String, String) {
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
        guard let deviceId = json?["device_id"] as? String,
              let patientId = json?["patient_id"] as? String else {
            throw PairingError.invalidResponse
        }

        return (deviceId, patientId)
    }
}
