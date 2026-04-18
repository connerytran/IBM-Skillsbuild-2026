import { useState, useEffect, useRef } from 'react';

interface Alert {
  id: string;
  type: 'warning' | 'success';
  title: string;
  description: string;
  timestamp: Date;
}


function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
}

export default function App() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [connected, setConnected] = useState(false);
  const [flightId, setFlightId] = useState<string | null>(null);
  const alertsScrollRef = useRef<HTMLDivElement>(null);

  // Show scrollbar only during active scroll
  useEffect(() => {
    const el = alertsScrollRef.current;
    if (!el) return;
    let timeout: ReturnType<typeof setTimeout>;
    const onScroll = () => {
      el.classList.add('is-scrolling');
      clearTimeout(timeout);
      timeout = setTimeout(() => el.classList.remove('is-scrolling'), 800);
    };
    el.addEventListener('scroll', onScroll);
    return () => { el.removeEventListener('scroll', onScroll); clearTimeout(timeout); };
  }, []);

  // WebSocket connection to agent backend
  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: ReturnType<typeof setTimeout>;
    let cancelled = false;

    function connect() {
      ws = new WebSocket('ws://localhost:8765');

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'recommendation') {
            const content: string = data.content ?? '';
            const lowerContent = content.toLowerCase();
            const isWarning = /\b(do not|don't|wait|hold|delay|cannot|can't|not yet|caution)\b/.test(lowerContent);
            if (data.flight_id) setFlightId(data.flight_id);
            const newAlert: Alert = {
              id: `alert-${Date.now()}`,
              type: isWarning ? 'warning' : 'success',
              title: '',
              description: content,
              timestamp: new Date(data.timestamp ?? Date.now()),
            };
            setAlerts(prev => [newAlert, ...prev]);
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (!cancelled) {
          reconnectTimeout = setTimeout(connect, 3000);
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, []);

  // Update current time
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen w-full overflow-hidden flex items-center justify-center p-8" style={{
      fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, sans-serif",
      background: 'linear-gradient(135deg, #F0F2F5 0%, #F8F9FA 100%)'
    }}>
      <div
        className="w-full max-w-5xl relative flex flex-col"
        style={{
          background: '#F8F9FA',
          border: '1px solid #E0E0E0',
          borderRadius: '8px',
          padding: '20px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)',
          maxHeight: 'calc(100vh - 4rem)',
        }}
      >
        {/* Subtle grid pattern overlay */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.015]"
          style={{
            backgroundImage: `
              linear-gradient(to right, #2C2C2A 1px, transparent 1px),
              linear-gradient(to bottom, #2C2C2A 1px, transparent 1px)
            `,
            backgroundSize: '24px 24px',
            borderRadius: '8px',
          }}
        />

        {/* Header */}
        <div className="flex items-start justify-between mb-6 relative">
          <div>
            <div
              className="mb-1.5"
              style={{
                fontSize: '18px',
                fontWeight: 500,
                color: '#2C2C2A',
                fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: '-0.01em'
              }}
            >
              {flightId ? `Flight ${flightId}` : 'Gate Monitor'}
            </div>
            <div
              style={{
                fontSize: '13px',
                color: '#5F5E5A',
                letterSpacing: '0.01em'
              }}
            >
              {flightId ? `Recommendations for ${flightId}` : 'Waiting for connection...'}
            </div>
          </div>
          <div className="text-right">
            <div
              className="mb-0.5 tabular-nums"
              style={{
                fontSize: '14px',
                color: '#5F5E5A',
                fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: '0.02em'
              }}
            >
              {formatTime(currentTime)}
            </div>
            <div
              style={{
                fontSize: '11px',
                color: '#888780',
                letterSpacing: '0.02em',
                textTransform: 'uppercase'
              }}
            >
              Current time
            </div>
          </div>
        </div>

        {/* Live indicator */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: connected ? '#639922' : '#D94F3D' }}
            />
            <div style={{ fontSize: '11px', color: '#888780', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Live Agent Feed
            </div>
          </div>
          {alerts.length > 0 && (
            <button
              onClick={() => setAlerts([])}
              style={{
                fontSize: '11px',
                color: '#888780',
                letterSpacing: '0.03em',
                textTransform: 'uppercase',
                background: 'none',
                border: '1px solid #E0E0E0',
                borderRadius: '4px',
                padding: '3px 8px',
                cursor: 'pointer',
              }}
            >
              Clear
            </button>
          )}
        </div>

        {/* Alert Cards */}
        <div ref={alertsScrollRef} className="alerts-scroll" style={{ display: 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto', flex: 1 }}>
          {alerts.length === 0 && (
            <div
              style={{
                padding: '32px',
                textAlign: 'center',
                color: '#888780',
                fontSize: '13px',
                letterSpacing: '0.01em',
              }}
            >
              Waiting for agent recommendations...
            </div>
          )}
          {alerts.map((alert, index) => (
            <div
              key={alert.id}
              style={{
                backgroundColor: '#F0F4FF',
                border: '1px solid #D8E0F5',
                borderRadius: '6px',
                padding: '12px 16px',
                animation: `slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.05}s backwards`,
              }}
            >
              {/* Description */}
              {(() => {
                const lines = alert.description.split('\n').filter(l => l.trim());
                const headlineIndex = lines.findLastIndex(l => /^\[?(CLOSE GATE|HOLD GATE|OPEN GATE)/i.test(l.trim()));
                const headline = headlineIndex >= 0 ? lines[headlineIndex] : '';
                const summary = headlineIndex >= 0 && headlineIndex + 1 < lines.length ? lines[headlineIndex + 1] : '';
                const bullets = lines.filter((_, i) => i !== headlineIndex && i !== headlineIndex + 1);
                return (
                  <>
                    <div className="flex items-baseline justify-between gap-4" style={{ marginBottom: '4px' }}>
                      <div style={{ fontSize: '14px', fontWeight: 600, color: '#1A1A1A' }}>
                        {headline}
                      </div>
                      <span style={{ fontSize: '11px', color: '#ABABAB', fontFamily: "'JetBrains Mono', monospace", flexShrink: 0 }}>
                        {formatTime(alert.timestamp)}
                      </span>
                    </div>
                    {summary && (
                      <div style={{ fontSize: '12px', color: '#6B6B6B', marginBottom: '8px' }}>
                        {summary}
                      </div>
                    )}
                    <div style={{ fontSize: '12px', color: '#6B6B6B', lineHeight: '1.6', whiteSpace: 'pre-line' }}>
                      {bullets.join('\n')}
                    </div>
                  </>
                );
              })()}
            </div>
          ))}
        </div>
      </div>

      <style>{`
        .alerts-scroll::-webkit-scrollbar {
          width: 4px;
        }
        .alerts-scroll::-webkit-scrollbar-track {
          background: transparent;
        }
        .alerts-scroll::-webkit-scrollbar-thumb {
          background: transparent;
          border-radius: 999px;
          transition: background 1.2s ease;
        }
        .alerts-scroll.is-scrolling::-webkit-scrollbar-thumb {
          background: #A0AACF;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-8px) scale(0.98);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }

        @keyframes ping {
          0% {
            transform: scale(1);
            opacity: 1;
          }
          75%, 100% {
            transform: scale(2);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
}