import Foundation
import Combine

class WebSocketService: ObservableObject {
    @Published var isConnected = false
    @Published var connectionError: String?

    private var webSocketTask: URLSessionWebSocketTask?
    private let deviceId: String
    private let baseURL = "wss://api-haven.onrender.com/ws/wearable"  // Update with your backend URL

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
            "vitals": try? JSONSerialization.jsonObject(with: data) as Any
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
