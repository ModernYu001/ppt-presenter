import React, { useEffect, useState } from 'react';

const API_BASE = 'http://127.0.0.1:18765/api';

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function extractApiError(err) {
  const text = String(err?.message || err || 'Request failed');
  const detailMatch = text.match(/"detail":"([^"]+)"/);
  if (detailMatch) return detailMatch[1];
  return text;
}

export default function App() {
  const [modelStatus, setModelStatus] = useState('Idle');
  const [config, setConfig] = useState({
    base_url: '',
    api_key: '',
    model: '',
    tts_provider: 'local',
    voice_profile: '',
    elevenlabs_api_key: '',
    elevenlabs_voice_id: '',
    elevenlabs_model_id: 'eleven_multilingual_v2',
  });
  const [models, setModels] = useState([]);
  const [pptPath, setPptPath] = useState('');
  const [pptStatus, setPptStatus] = useState('No deck loaded');
  const [slides, setSlides] = useState([]);
  const [narration, setNarration] = useState('');
  const [presentationState, setPresentationState] = useState({});
  const [presentationBusy, setPresentationBusy] = useState(false);
  const [cloneName, setCloneName] = useState('');
  const [cloneSamples, setCloneSamples] = useState('');
  const [cloneStatus, setCloneStatus] = useState('');
  const platform = presentationState.platform || 'unknown';
  const supportsSlideshowControl = Boolean(presentationState.supports_slideshow_control);
  const showMacNote = platform !== 'win32';

  const refreshPresentationState = async () => {
    const state = await apiGet('/presentation/state');
    setPresentationState(state);
    if (state.last_narration) setNarration(state.last_narration);
    return state;
  };

  useEffect(() => {
    (async () => {
      try {
        const cfg = await apiGet('/config');
        setConfig(cfg);
        await refreshPresentationState();
      } catch (err) {
        setModelStatus(`Backend not ready: ${err.message}`);
      }
    })();
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        await refreshPresentationState();
      } catch {
        // ignore
      }
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  const saveConfig = async () => {
    await apiPost('/config', config);
    setModelStatus('Settings saved');
  };

  const discoverModels = async () => {
    setModelStatus('Discovering models...');
    const data = await apiPost('/models/discover', {
      base_url: config.base_url,
      api_key: config.api_key,
    });
    setModels(data.models || []);
    setModelStatus(`Loaded ${data.models?.length || 0} model(s)`);
  };

  const loadPpt = async () => {
    const data = await apiPost('/ppt/load', { path: pptPath });
    setSlides(data.slides || []);
    setPptStatus(`Loaded ${data.slides?.length || 0} slide(s)`);
  };

  const openPpt = async () => {
    setPresentationBusy(true);
    try {
      const state = await apiPost('/ppt/open', { path: pptPath });
      setPresentationState(state);
      const statusText = state.supports_slideshow_control
        ? `PowerPoint ready: ${state.deck_path}`
        : `Presentation opened in macOS app: ${state.deck_path}`;
      setPptStatus(statusText);
    } catch (err) {
      setPptStatus(`Open failed: ${extractApiError(err)}`);
    } finally {
      setPresentationBusy(false);
    }
  };

  const startShow = async () => {
    setPresentationBusy(true);
    try {
      const state = await apiPost('/presentation/start');
      setPresentationState(state);
      setPptStatus('Slide show started');
    } catch (err) {
      setPptStatus(`Start failed: ${extractApiError(err)}`);
    } finally {
      setPresentationBusy(false);
    }
  };

  const nextSlide = async () => {
    setPresentationBusy(true);
    try {
      const state = await apiPost('/presentation/next');
      setPresentationState(state);
    } catch (err) {
      setPptStatus(`Next failed: ${extractApiError(err)}`);
    } finally {
      setPresentationBusy(false);
    }
  };

  const autoStart = async () => {
    setPresentationBusy(true);
    try {
      await saveConfig();
      const state = await apiPost('/presentation/auto-start');
      setPresentationState(state);
    } catch (err) {
      setPptStatus(`Auto present failed: ${extractApiError(err)}`);
    } finally {
      setPresentationBusy(false);
    }
  };

  const autoStop = async () => {
    setPresentationBusy(true);
    try {
      const state = await apiPost('/presentation/auto-stop');
      setPresentationState(state);
    } catch (err) {
      setPptStatus(`Stop failed: ${extractApiError(err)}`);
    } finally {
      setPresentationBusy(false);
    }
  };

  const generateNarration = async () => {
    const state = await apiGet('/presentation/state');
    const slideIndex = state.current_slide || 1;
    const slide = slides.find((s) => s.index === slideIndex) || slides[0];
    if (!slide) throw new Error('No slide loaded');
    const data = await apiPost('/narration/generate', {
      slide_index: slide.index,
      text: slide.text || '',
      notes: slide.notes || '',
      style: 'professional',
      duration_hint_sec: 45,
    });
    setNarration(data.text || '');
  };

  const testTts = async () => {
    const text = narration || '这是一段测试播报。';
    if (config.tts_provider === 'elevenlabs') {
      await apiPost('/tts/elevenlabs/speak', {
        text,
        api_key: config.elevenlabs_api_key,
        voice_id: config.elevenlabs_voice_id,
        model_id: config.elevenlabs_model_id,
      });
    } else {
      await apiPost('/tts/speak', {
        text,
        voice_id: config.voice_profile,
        rate: 185,
        volume: 1.0,
      });
    }
  };

  const createClone = async () => {
    setCloneStatus('Creating voice clone...');
    try {
      await saveConfig();
      const sample_paths = cloneSamples
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const data = await apiPost('/tts/elevenlabs/create-voice', {
        name: cloneName || 'PPT Presenter Voice',
        description: 'Created by PPT Auto Presenter',
        sample_paths,
        api_key: config.elevenlabs_api_key,
      });
      if (data.voice_id) {
        setConfig((prev) => ({ ...prev, elevenlabs_voice_id: data.voice_id }));
      }
      setCloneStatus('Clone created');
    } catch (err) {
      setCloneStatus(`Clone failed: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-ink p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold">PPT Auto Presenter</h1>
            <p className="text-slate-400">Beautiful control console for model-driven presentations.</p>
          </div>
          <div className="flex gap-2">
            <span className="tag">Backend: 127.0.0.1:18765</span>
            <span className="tag">Provider: {config.tts_provider}</span>
            <span className="tag">Platform: {platform}</span>
          </div>
        </header>

        {showMacNote && (
          <section className="notice-card">
            <p className="label">Platform note</p>
            <h2 className="text-lg font-semibold">macOS and non-Windows mode</h2>
            <p className="mt-2 text-sm text-slate-300">
              This platform opens the PPTX with the system <code>open</code> flow and keeps narration features available,
              but slide show start, slide navigation, and auto-present controls stay disabled because PowerPoint COM is
              Windows-only.
            </p>
          </section>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section className="card space-y-4">
            <div>
              <p className="label">Model settings</p>
              <h2 className="text-xl font-semibold">LLM Endpoint</h2>
            </div>
            <div className="space-y-3">
              <input className="input" placeholder="Base URL" value={config.base_url || ''} onChange={(e) => setConfig({ ...config, base_url: e.target.value })} />
              <input className="input" placeholder="API Key" value={config.api_key || ''} onChange={(e) => setConfig({ ...config, api_key: e.target.value })} />
              <select className="input" value={config.model || ''} onChange={(e) => setConfig({ ...config, model: e.target.value })}>
                <option value="">Select model</option>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>{m.id}</option>
                ))}
              </select>
              <div className="flex gap-2">
                <button className="button" onClick={discoverModels}>Discover</button>
                <button className="button-secondary" onClick={saveConfig}>Save</button>
              </div>
              <p className="text-xs text-slate-400">{modelStatus}</p>
            </div>
          </section>

          <section className="card space-y-4">
            <div>
              <p className="label">Voice &amp; TTS</p>
              <h2 className="text-xl font-semibold">Speech Provider</h2>
            </div>
            <div className="space-y-3">
              <select className="input" value={config.tts_provider || 'local'} onChange={(e) => setConfig({ ...config, tts_provider: e.target.value })}>
                <option value="local">Local TTS</option>
                <option value="elevenlabs">ElevenLabs</option>
              </select>
              <input className="input" placeholder="Local voice id" value={config.voice_profile || ''} onChange={(e) => setConfig({ ...config, voice_profile: e.target.value })} />
              <input className="input" placeholder="ElevenLabs API key" value={config.elevenlabs_api_key || ''} onChange={(e) => setConfig({ ...config, elevenlabs_api_key: e.target.value })} />
              <input className="input" placeholder="ElevenLabs voice id" value={config.elevenlabs_voice_id || ''} onChange={(e) => setConfig({ ...config, elevenlabs_voice_id: e.target.value })} />
              <input className="input" placeholder="ElevenLabs model id" value={config.elevenlabs_model_id || ''} onChange={(e) => setConfig({ ...config, elevenlabs_model_id: e.target.value })} />
              <button className="button" onClick={testTts}>Test TTS</button>
            </div>
            <div className="space-y-3 border-t border-line pt-4">
              <p className="label">ElevenLabs Clone</p>
              <input className="input" placeholder="Clone voice name" value={cloneName} onChange={(e) => setCloneName(e.target.value)} />
              <textarea className="input min-h-[90px]" placeholder="Sample file paths (one per line)" value={cloneSamples} onChange={(e) => setCloneSamples(e.target.value)} />
              <button className="button-secondary" onClick={createClone}>Create Clone</button>
              <p className="text-xs text-slate-400">{cloneStatus}</p>
            </div>
          </section>

          <section className="card space-y-4">
            <div>
              <p className="label">Presentation</p>
              <h2 className="text-xl font-semibold">Deck &amp; Narration</h2>
            </div>
            <div className="space-y-3">
              <input className="input" placeholder="PPTX path" value={pptPath} onChange={(e) => setPptPath(e.target.value)} />
              <div className="flex gap-2">
                <button className="button" onClick={loadPpt}>Load PPT</button>
                <button className="button-secondary" onClick={openPpt} disabled={presentationBusy}>
                  {supportsSlideshowControl ? 'Open PPT' : 'Open PPTX'}
                </button>
              </div>
              <div className="flex gap-2">
                <button className="button-secondary" onClick={startShow} disabled={presentationBusy || !supportsSlideshowControl}>Start Show</button>
                <button className="button-secondary" onClick={nextSlide} disabled={presentationBusy || !supportsSlideshowControl}>Next Slide</button>
              </div>
              <div className="flex gap-2">
                <button className="button" onClick={autoStart} disabled={presentationBusy || !supportsSlideshowControl}>Auto Present</button>
                <button className="button-secondary" onClick={autoStop} disabled={presentationBusy}>Stop Auto</button>
              </div>
              <button className="button-secondary" onClick={generateNarration}>Generate Narration</button>
              <p className="text-xs text-slate-400">{pptStatus}</p>
              <div className="rounded-xl border border-line bg-panel2 p-3 text-xs text-slate-300 space-y-1">
                <div>State: {presentationState.status || 'idle'}</div>
                <div>Slide: {presentationState.current_slide ?? '-'}</div>
                <div>Auto: {String(presentationState.auto_mode ?? false)}</div>
                <div>Speaking: {String(presentationState.speaking ?? false)}</div>
                <div>Control: {String(presentationState.supports_slideshow_control ?? false)}</div>
                <div>Open Mode: {presentationState.open_strategy ?? '-'}</div>
                <div>Deck: {presentationState.deck_path ?? '-'}</div>
                <div>Last Narration: {presentationState.last_generated_slide ?? '-'}</div>
                <div>Error: {presentationState.error || '-'}</div>
              </div>
            </div>
          </section>
        </div>

        <section className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="label">Narration Output</p>
              <h3 className="text-lg font-semibold">Current Slide Script</h3>
            </div>
            <span className="tag">Slides loaded: {slides.length}</span>
          </div>
          <textarea className="mt-4 h-48 w-full rounded-xl border border-line bg-panel2 p-4 text-sm text-slate-100" value={narration} onChange={(e) => setNarration(e.target.value)} />
        </section>
      </div>
    </div>
  );
}
