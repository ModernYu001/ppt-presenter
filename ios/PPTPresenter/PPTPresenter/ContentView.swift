import SwiftUI
import AVKit
import UniformTypeIdentifiers

struct ContentView: View {
    @EnvironmentObject var settings: AppSettings

    var body: some View {
        TabView {
            UploadView()
                .tabItem {
                    Label("演示", systemImage: "play.rectangle.fill")
                }

            HistoryView()
                .tabItem {
                    Label("历史", systemImage: "clock.fill")
                }

            SettingsView()
                .tabItem {
                    Label("设置", systemImage: "gear")
                }
        }
        .tint(.green)
    }
}

// MARK: - Upload View

struct UploadView: View {
    @EnvironmentObject var settings: AppSettings
    @State private var isImporting = false
    @State private var jobId: String?
    @State private var jobStatus: JobStatus?
    @State private var errorMsg: String?
    @State private var isPolling = false
    @State private var showPlayer = false

    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                Spacer()

                // Logo area
                VStack(spacing: 8) {
                    Image(systemName: "doc.richtext")
                        .font(.system(size: 64))
                        .foregroundColor(.green)
                    Text("PPT 自动演示")
                        .font(.title2.bold())
                    Text("上传 PPT → AI 解说 → 语音播报 → 自动翻页视频")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }

                // Upload button
                if jobId == nil || jobStatus?.status == "done" || jobStatus?.status == "failed" {
                    Button(action: { isImporting = true }) {
                        HStack {
                            Image(systemName: "square.and.arrow.up")
                            Text("选择 PPT 文件")
                        }
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .padding(.horizontal, 40)
                }

                // Progress
                if let status = jobStatus, status.status != "done" && status.status != "failed" {
                    VStack(spacing: 12) {
                        ProgressView(value: Double(status.progress), total: 100)
                            .tint(.green)

                        HStack {
                            Text(statusLabel(status.status))
                                .font(.subheadline.bold())
                            Spacer()
                            Text("\(status.progress)%")
                                .font(.caption.monospacedDigit())
                                .foregroundColor(.secondary)
                        }

                        if !status.current_step.isEmpty {
                            Text(status.current_step)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.horizontal, 40)
                }

                // Done → Play
                if let status = jobStatus, status.status == "done" {
                    VStack(spacing: 12) {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 48))
                            .foregroundColor(.green)
                        Text("演示视频已生成")
                            .font(.headline)
                        Text("\(status.total_slides) 页 · \(String(format: "%.1f", status.output_size_mb)) MB")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Button(action: { showPlayer = true }) {
                            HStack {
                                Image(systemName: "play.fill")
                                Text("播放演示")
                            }
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(12)
                        }
                        .padding(.horizontal, 40)
                    }
                }

                // Error
                if let status = jobStatus, status.status == "failed" {
                    VStack(spacing: 8) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 36))
                            .foregroundColor(.red)
                        Text("处理失败")
                            .font(.headline)
                        Text(status.error)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.horizontal, 40)
                }

                if let err = errorMsg {
                    Text(err)
                        .font(.caption)
                        .foregroundColor(.red)
                        .padding(.horizontal)
                }

                Spacer()
            }
            .navigationTitle("PPT Presenter")
            .fileImporter(
                isPresented: $isImporting,
                allowedContentTypes: [UTType.presentation, .data],
                allowsMultipleSelection: false
            ) { result in
                handleImport(result)
            }
            .fullScreenCover(isPresented: $showPlayer) {
                if let jid = jobId {
                    VideoPlayerView(
                        url: APIService(settings: settings).downloadURL(jobId: jid)
                    )
                }
            }
        }
    }

    private func statusLabel(_ s: String) -> String {
        switch s {
        case "queued": return "⏳ 排队中"
        case "parsing": return "📄 解析 PPT"
        case "rendering": return "🖼️ 渲染页面"
        case "narrating": return "🤖 AI 生成解说"
        case "synthesizing": return "🎙️ 语音合成"
        case "stitching": return "🎬 合成视频"
        default: return s
        }
    }

    private func handleImport(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            guard let url = urls.first else { return }
            guard url.startAccessingSecurityScopedResource() else {
                errorMsg = "无法访问文件"
                return
            }
            defer { url.stopAccessingSecurityScopedResource() }
            uploadFile(url)
        case .failure(let error):
            errorMsg = error.localizedDescription
        }
    }

    private func uploadFile(_ url: URL) {
        errorMsg = nil
        jobStatus = nil
        jobId = nil

        let api = APIService(settings: settings)
        Task {
            do {
                let resp = try await api.upload(fileURL: url, voice: settings.voiceId)
                jobId = resp.job_id
                startPolling()
            } catch {
                errorMsg = "上传失败: \(error.localizedDescription)"
            }
        }
    }

    private func startPolling() {
        guard !isPolling, let jid = jobId else { return }
        isPolling = true
        let api = APIService(settings: settings)

        Task {
            while isPolling {
                do {
                    let status = try await api.status(jobId: jid)
                    await MainActor.run { jobStatus = status }
                    if status.status == "done" || status.status == "failed" {
                        isPolling = false
                        break
                    }
                } catch {
                    // ignore transient errors
                }
                try? await Task.sleep(nanoseconds: 2_000_000_000) // 2s
            }
        }
    }
}

// MARK: - Video Player

struct VideoPlayerView: View {
    let url: URL
    @Environment(\.dismiss) var dismiss

    var body: some View {
        ZStack(alignment: .topTrailing) {
            VideoPlayer(player: AVPlayer(url: url))
                .ignoresSafeArea()

            Button(action: { dismiss() }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.title)
                    .foregroundColor(.white)
                    .shadow(radius: 4)
            }
            .padding()
        }
    }
}

// MARK: - History View

struct HistoryView: View {
    @EnvironmentObject var settings: AppSettings
    @State private var jobs: [JobStatus] = []
    @State private var isLoading = false

    var body: some View {
        NavigationView {
            List {
                if jobs.isEmpty && !isLoading {
                    Text("暂无历史记录")
                        .foregroundColor(.secondary)
                }
                ForEach(jobs) { job in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(job.filename)
                                .font(.subheadline.bold())
                            Text("\(job.total_slides) 页 · \(statusEmoji(job.status)) \(job.status)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text(dateString(job.created_at))
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        if job.status == "done" {
                            Text("\(String(format: "%.1f", job.output_size_mb)) MB")
                                .font(.caption.monospacedDigit())
                                .foregroundColor(.green)
                        }
                    }
                }
                .onDelete(perform: deleteJobs)
            }
            .navigationTitle("历史记录")
            .refreshable { await loadJobs() }
            .task { await loadJobs() }
        }
    }

    private func statusEmoji(_ s: String) -> String {
        switch s {
        case "done": return "✅"
        case "failed": return "❌"
        default: return "⏳"
        }
    }

    private func dateString(_ ts: Double) -> String {
        let date = Date(timeIntervalSince1970: ts)
        let fmt = DateFormatter()
        fmt.dateFormat = "MM/dd HH:mm"
        return fmt.string(from: date)
    }

    private func loadJobs() async {
        isLoading = true
        defer { isLoading = false }
        let api = APIService(settings: settings)
        do {
            jobs = try await api.listJobs()
        } catch {}
    }

    private func deleteJobs(at offsets: IndexSet) {
        let api = APIService(settings: settings)
        for idx in offsets {
            let job = jobs[idx]
            Task {
                try? await api.deleteJob(jobId: job.job_id)
            }
        }
        jobs.remove(atOffsets: offsets)
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @EnvironmentObject var settings: AppSettings

    var body: some View {
        NavigationView {
            Form {
                Section("服务器") {
                    TextField("服务器地址", text: $settings.serverURL)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                    TextField("认证 Token", text: $settings.authToken)
                        .textInputAutocapitalization(.never)
                }

                Section("语音") {
                    Picker("播报声音", selection: $settings.voiceId) {
                        ForEach(AppSettings.voices, id: \.id) { voice in
                            Text(voice.label).tag(voice.id)
                        }
                    }
                }

                Section("关于") {
                    HStack {
                        Text("版本")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("设置")
        }
    }
}
