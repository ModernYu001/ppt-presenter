import httpx


class ModelService:
    def __init__(self, config_service):
        self.config_service = config_service

    async def discover_models(self, base_url: str, api_key: str = ""):
        base_url = base_url.rstrip("/")
        headers = self._headers(api_key)
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{base_url}/models", headers=headers)
            response.raise_for_status()
            data = response.json()
        models = data.get("data", [])
        return [
            {
                "id": item.get("id", ""),
                "owned_by": item.get("owned_by", ""),
            }
            for item in models
        ]

    async def generate_narration(self, slide_index: int, text: str, notes: str = "", style: str = "professional", duration_hint_sec: int = 45):
        config = self.config_service.load()
        base_url = (config.get("base_url") or "").rstrip("/")
        api_key = config.get("api_key") or ""
        model = config.get("model") or ""
        if not base_url or not model:
            raise ValueError("Missing base_url or model in config")

        prompt = self._build_prompt(slide_index, text, notes, style, duration_hint_sec)
        headers = self._headers(api_key)
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an excellent live presentation speaker. Produce natural, clear spoken narration for the current slide in Chinese unless the slide is clearly in another language. Keep it audience-facing, concise, and smooth to read aloud.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.7,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise ValueError(f"Unexpected model response: {exc}")

    def _headers(self, api_key: str):
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _build_prompt(self, slide_index: int, text: str, notes: str, style: str, duration_hint_sec: int):
        return (
            f"请为第 {slide_index} 页 PPT 生成适合现场演讲的中文讲稿。\n"
            f"要求：风格={style}；目标时长约 {duration_hint_sec} 秒；口语化、流畅、不要机械复述；"
            "如果备注区有信息，优先吸收备注区意图；如果页内信息较少，可以做合理过渡和解释，但不要编造数据。\n\n"
            f"【页面文字】\n{text or '(无)'}\n\n"
            f"【备注】\n{notes or '(无)'}\n\n"
            "只输出最终讲稿正文。"
        )
