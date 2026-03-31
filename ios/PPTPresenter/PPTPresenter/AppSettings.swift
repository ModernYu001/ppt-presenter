import Foundation
import SwiftUI

class AppSettings: ObservableObject {
    @AppStorage("serverURL") var serverURL: String = "https://modernyu.org"
    @AppStorage("authToken") var authToken: String = "ppt-presenter-2026"
    @AppStorage("voiceId") var voiceId: String = "zh-CN-XiaoxiaoNeural"

    var apiBaseURL: String {
        serverURL.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    }

    static let voices: [(id: String, label: String)] = [
        ("zh-CN-XiaoxiaoNeural", "晓晓 (女·温暖)"),
        ("zh-CN-XiaoyiNeural", "晓艺 (女·活泼)"),
        ("zh-CN-YunxiNeural", "云希 (男·专业)"),
        ("zh-CN-YunjianNeural", "云健 (男·沉稳)"),
        ("en-US-JennyNeural", "Jenny (F·Friendly)"),
        ("en-US-GuyNeural", "Guy (M·Professional)"),
    ]
}
