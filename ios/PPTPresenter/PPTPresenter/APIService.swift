import Foundation

struct UploadResponse: Codable {
    let job_id: String
    let status: String
    let filename: String
}

struct JobStatus: Codable, Identifiable {
    var id: String { job_id }
    let job_id: String
    let filename: String
    let size_mb: Double
    let voice: String
    let status: String
    let progress: Int
    let total_slides: Int
    let current_step: String
    let error: String
    let output_size_mb: Double
    let created_at: Double
    let completed_at: Double?
}

struct JobListResponse: Codable {
    let jobs: [JobStatus]
}

class APIService {
    let settings: AppSettings

    init(settings: AppSettings) {
        self.settings = settings
    }

    private var headers: [String: String] {
        ["Authorization": "Bearer \(settings.authToken)"]
    }

    // MARK: - Upload PPTX

    func upload(fileURL: URL, voice: String) async throws -> UploadResponse {
        let url = URL(string: "\(settings.apiBaseURL)/api/headless/upload?voice=\(voice)")!

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        for (k, v) in headers { request.setValue(v, forHTTPHeaderField: k) }

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        let fileData = try Data(contentsOf: fileURL)
        let filename = fileURL.lastPathComponent

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            let msg = String(data: data, encoding: .utf8) ?? "Upload failed"
            throw NSError(domain: "API", code: -1, userInfo: [NSLocalizedDescriptionKey: msg])
        }
        return try JSONDecoder().decode(UploadResponse.self, from: data)
    }

    // MARK: - Job Status

    func status(jobId: String) async throws -> JobStatus {
        let url = URL(string: "\(settings.apiBaseURL)/api/headless/status/\(jobId)")!
        var request = URLRequest(url: url)
        for (k, v) in headers { request.setValue(v, forHTTPHeaderField: k) }

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(JobStatus.self, from: data)
    }

    // MARK: - List Jobs

    func listJobs() async throws -> [JobStatus] {
        let url = URL(string: "\(settings.apiBaseURL)/api/headless/jobs")!
        var request = URLRequest(url: url)
        for (k, v) in headers { request.setValue(v, forHTTPHeaderField: k) }

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(JobListResponse.self, from: data).jobs
    }

    // MARK: - Download URL

    func downloadURL(jobId: String) -> URL {
        URL(string: "\(settings.apiBaseURL)/api/headless/download/\(jobId)?token=\(settings.authToken)")!
    }

    // MARK: - Delete Job

    func deleteJob(jobId: String) async throws {
        let url = URL(string: "\(settings.apiBaseURL)/api/headless/jobs/\(jobId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        for (k, v) in headers { request.setValue(v, forHTTPHeaderField: k) }
        let _ = try await URLSession.shared.data(for: request)
    }
}
