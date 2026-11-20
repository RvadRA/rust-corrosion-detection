import React, { useState, useEffect, useRef } from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Cog, 
  UploadCloud, 
  Download, 
  RefreshCw, 
  Maximize2, 
  Layers, 
  FileImage, 
  Eye, 
  Activity,
  Calendar,
  Crosshair
} from 'lucide-react';

const API_BASE = '';

export default function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentResult, setCurrentResult] = useState(null);
  const [activeTab, setActiveTab] = useState('overlay'); // 'overlay' | 'original' | 'mask'
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);

  const fileInputRef = useRef(null);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setSystemHealth(data);
      } else {
        setSystemHealth({ status: 'error', db: 'error', ml: 'error' });
      }
    } catch {
      setSystemHealth({ status: 'offline', db: 'unreachable', ml: 'unreachable' });
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/results?limit=25`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data.items || []);
      }
    } catch (e) {
      console.error('Ошибка загрузки истории:', e);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    fetchHistory();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleInspect = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Пожалуйста, выберите файл изображения');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${API_BASE}/api/v1/inspect`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Ошибка сервера (${res.status})`);
      }

      const result = await res.json();
      setCurrentResult(result);
      setActiveTab('overlay');
      fetchHistory();
    } catch (err) {
      setError(err.message || 'Сбой при отправке запроса инспекции');
    } finally {
      setLoading(false);
    }
  };

  const selectHistoryItem = (item) => {
    setCurrentResult(item);
    setActiveTab('overlay');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const renderVerdictBadge = (verdict) => {
    switch (verdict) {
      case 'НОРМА':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-4 h-4" /> НОРМА
          </span>
        );
      case 'ВНИМАНИЕ':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wider bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-4 h-4" /> ВНИМАНИЕ
          </span>
        );
      case 'БРАК':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wider bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <XCircle className="w-4 h-4" /> БРАК
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wider bg-slate-500/15 text-slate-300 border border-slate-500/30">
            <Cog className="w-4 h-4" /> {verdict || 'ОШИБКА'}
          </span>
        );
    }
  };

  const getActiveImageUrl = () => {
    if (!currentResult) return '';
    if (activeTab === 'mask') return `${API_BASE}${currentResult.mask_url}`;
    if (activeTab === 'original') {
      return currentResult.original_url 
        ? `${API_BASE}${currentResult.original_url}` 
        : previewUrl || `${API_BASE}${currentResult.overlay_url}`;
    }
    return `${API_BASE}${currentResult.overlay_url}`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Шапка системы */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
              <Crosshair className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-white">
                  Система контроля коррозии и ржавчины
                </h1>
                <span className="px-2 py-0.5 text-[10px] font-semibold bg-blue-500/20 text-blue-300 rounded border border-blue-500/30">
                  КТ 4 • Прототип
                </span>
              </div>
              <p className="text-xs text-slate-400">
                ЮУрГУ • Автоматический контроль цилиндров линии ПАО «ЧКПЗ» (U-Net)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-slate-900/80 border border-slate-800 rounded-lg px-4 py-2 text-xs">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${systemHealth?.status === 'ok' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`}></span>
              <span className="font-medium text-slate-200">
                {systemHealth?.status === 'ok' ? 'Сервисы активны' : 'Сбой сервисов'}
              </span>
            </div>
            <div className="h-3 w-px bg-slate-800"></div>
            <div className="text-slate-400 space-x-2">
              <span>БД: <strong className={systemHealth?.db === 'connected' ? 'text-emerald-400' : 'text-rose-400'}>{systemHealth?.db || '—'}</strong></span>
              <span>•</span>
              <span>ML: <strong className={systemHealth?.ml === 'ready' ? 'text-emerald-400' : 'text-rose-400'}>{systemHealth?.ml || '—'}</strong></span>
              <span>•</span>
              <span>Архив: <strong className="text-slate-300">{systemHealth?.retention_days || 30} дн.</strong></span>
            </div>
          </div>
        </div>
      </header>

      {/* Основной контент */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Левая секция: Контроль деталей (7 колонок) */}
        <section className="lg:col-span-7 flex flex-col gap-6">
          {/* Блок загрузки */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-blue-400" />
                Контроль детали
              </h2>
              <span className="text-xs text-slate-400">Форматы: JPG, PNG, WEBP (до 32 МБ)</span>
            </div>

            <form onSubmit={handleInspect} className="space-y-4">
              <div
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center ${
                  selectedFile 
                    ? 'border-blue-500/50 bg-blue-500/5' 
                    : 'border-slate-800 hover:border-blue-500/40 bg-slate-950/40 hover:bg-slate-900/60'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/bmp"
                  onChange={handleFileChange}
                  className="hidden"
                />

                {previewUrl ? (
                  <div className="flex flex-col items-center">
                    <img
                      src={previewUrl}
                      alt="Превью детали"
                      className="max-h-48 rounded-lg object-contain border border-slate-700 shadow-md mb-3"
                    />
                    <p className="text-xs font-semibold text-slate-200">{selectedFile?.name}</p>
                    <p className="text-[11px] text-slate-400">{(selectedFile?.size / 1024).toFixed(1)} КБ • Нажмите для замены</p>
                  </div>
                ) : (
                  <div className="py-4 flex flex-col items-center">
                    <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-300 mb-3 border border-slate-700">
                      <FileImage className="w-6 h-6 text-blue-400" />
                    </div>
                    <p className="text-sm font-medium text-slate-200">Перетащите снимок цилиндра или выберите файл</p>
                    <p className="text-xs text-slate-400 mt-1">Изображение поступит на обработку модели U-Net (256×256)</p>
                  </div>
                )}
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                  <XCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={!selectedFile || loading}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm text-white transition shadow-lg shadow-blue-600/20 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Cog className="w-4 h-4 animate-spin" />
                      Выполняется сегментация U-Net...
                    </>
                  ) : (
                    <>
                      <Eye className="w-4 h-4" />
                      Запустить инспекцию
                    </>
                  )}
                </button>

                {selectedFile && !loading && (
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewUrl(null);
                    }}
                    className="py-2.5 px-4 rounded-xl border border-slate-800 hover:bg-slate-800 text-xs text-slate-300 transition"
                  >
                    Сброс
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* Результат текущей проверки */}
          {currentResult && (
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm space-y-5 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                <div>
                  <h2 className="text-base font-semibold text-white flex items-center gap-2">
                    <Activity className="w-5 h-5 text-blue-400" />
                    Результат инспекции
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">ID: {currentResult.id}</p>
                </div>
                <div>{renderVerdictBadge(currentResult.verdict)}</div>
              </div>

              {currentResult.message && (
                <div className={`p-3 rounded-xl border text-xs leading-relaxed ${
                  currentResult.verdict === 'ОШИБКА СИСТЕМЫ'
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                    : currentResult.calibrated 
                      ? 'bg-blue-500/10 border-blue-500/20 text-blue-200' 
                      : 'bg-amber-500/10 border-amber-500/20 text-amber-200'
                }`}>
                  {currentResult.message}
                </div>
              )}

              {/* Сетка метрик */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
                  <span className="text-[11px] font-medium text-slate-400">Площадь (px)</span>
                  <div className="text-base font-bold text-white mt-1">
                    {currentResult.area_px.toLocaleString()} <span className="text-xs font-normal text-slate-400">px</span>
                  </div>
                </div>

                <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
                  <span className="text-[11px] font-medium text-slate-400">Площадь (мм²)</span>
                  <div className="text-base font-bold text-white mt-1">
                    {currentResult.calibrated && currentResult.area_mm2 !== null
                      ? `${currentResult.area_mm2} мм²`
                      : <span className="text-xs font-normal text-amber-400">нет калибровки</span>}
                  </div>
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    {currentResult.calibrated ? 'Калибровано' : 'Нужен MM_PER_PX'}
                  </span>
                </div>

                <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
                  <span className="text-[11px] font-medium text-slate-400">Уверенность (Conf)</span>
                  <div className="text-base font-bold text-white mt-1">
                    {(currentResult.confidence * 100).toFixed(1)}%
                  </div>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Sigmoid U-Net</span>
                </div>

                <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
                  <span className="text-[11px] font-medium text-slate-400">Файл</span>
                  <div className="text-xs font-bold text-white mt-1 truncate" title={currentResult.filename}>
                    {currentResult.filename}
                  </div>
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    {new Date(currentResult.created_at).toLocaleTimeString('ru-RU')}
                  </span>
                </div>
              </div>

              {/* Просмотр масок и снимков */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-1.5 bg-slate-950/60 p-1 rounded-lg border border-slate-800 text-xs">
                    <button
                      type="button"
                      onClick={() => setActiveTab('overlay')}
                      className={`px-3 py-1.5 rounded-md font-medium transition ${
                        activeTab === 'overlay' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Overlay (Снимок + Маска)
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveTab('mask')}
                      className={`px-3 py-1.5 rounded-md font-medium transition ${
                        activeTab === 'mask' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Маска ржавчины
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveTab('original')}
                      className={`px-3 py-1.5 rounded-md font-medium transition ${
                        activeTab === 'original' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Исходный снимок
                    </button>
                  </div>

                  <a
                    href={getActiveImageUrl()}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium"
                  >
                    <Maximize2 className="w-3.5 h-3.5" /> В полном окне
                  </a>
                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden flex items-center justify-center min-h-[300px] p-2">
                  <img
                    src={getActiveImageUrl()}
                    alt="Изображение инспекции"
                    className="max-h-[420px] w-auto object-contain rounded-lg shadow-inner"
                  />
                </div>

                <div className="text-[11px] text-slate-400 flex items-center justify-between">
                  <span>🔴 Красная зона — сегментированная область ржавчины/коррозии (порог 0.5 + морфология)</span>
                  <span>Размер входа U-Net: 256×256 px</span>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Правая секция: Архив и история контроля (5 колонок) */}
        <section className="lg:col-span-5 flex flex-col">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm flex flex-col h-full">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-400" />
                  Архив проверок
                </h2>
                <p className="text-xs text-slate-400">PostgreSQL (хранение {systemHealth?.retention_days || 30} дней)</p>
              </div>

              <div className="flex items-center gap-2">
                <a
                  href={`${API_BASE}/api/v1/results.csv`}
                  download="results.csv"
                  className="px-2.5 py-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs font-medium flex items-center gap-1.5 transition"
                  title="Скачать реестр в CSV с UTF-8 BOM"
                >
                  <Download className="w-3.5 h-3.5" /> CSV
                </a>
                <button
                  type="button"
                  onClick={fetchHistory}
                  className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition"
                  title="Обновить журнал"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {historyLoading ? (
              <div className="flex-1 flex items-center justify-center text-xs text-slate-400 py-12">
                <Cog className="w-4 h-4 animate-spin mr-2" /> Загрузка журнала...
              </div>
            ) : history.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-xs text-slate-400 py-12 text-center">
                <Layers className="w-8 h-8 text-slate-600 mb-2" />
                Архив проверок пуст. Загрузите снимок для первой инспекции.
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto max-h-[640px] pr-1 space-y-2">
                {history.map((item) => {
                  const isSelected = currentResult?.id === item.id;
                  return (
                    <div
                      key={item.id}
                      onClick={() => selectHistoryItem(item)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                        isSelected 
                          ? 'bg-blue-600/15 border-blue-500/50 shadow-md' 
                          : 'bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700'
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-semibold text-slate-200 truncate" title={item.filename}>
                            {item.filename}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-2">
                          <span>{new Date(item.created_at).toLocaleTimeString('ru-RU')}</span>
                          <span>•</span>
                          <span>
                            {item.calibrated && item.area_mm2 !== null
                              ? `${item.area_mm2} мм²`
                              : `${item.area_px} px`}
                          </span>
                          <span>•</span>
                          <span>{(item.confidence * 100).toFixed(0)}% conf</span>
                        </div>
                      </div>

                      <div className="flex-shrink-0">
                        {renderVerdictBadge(item.verdict)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Подвал */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-400 bg-slate-950">
        Проектная работа «Современные методы DevOps» • ЮУрГУ 2026 • Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)
      </footer>
    </div>
  );
}
