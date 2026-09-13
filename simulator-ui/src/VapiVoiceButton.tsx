import { useState, useRef, useEffect } from 'react';
import Vapi from '@vapi-ai/web';
import './VapiVoiceButton.css';

export const VapiVoiceButton = () => {
  const [isActive, setIsActive] = useState(false);
  const [status, setStatus] = useState<string>('');
  const vapiRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      if (vapiRef.current) {
        vapiRef.current.removeAllListeners();
        if (isActive) {
          vapiRef.current.stop();
        }
      }
    };
  }, [isActive]);

  const toggleCall = async () => {
    if (isActive) {
      setStatus('Disconnecting...');
      vapiRef.current?.stop();
      return;
    }

    try {
      setStatus('Connecting...');
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://causen.onrender.com';
      const response = await fetch(`${baseUrl}/api/vapi/token`);
      if (!response.ok) {
        throw new Error(`Failed to fetch Vapi key: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.status !== "success" || !data.vapi_response || !data.vapi_response.token) {
        throw new Error("Invalid response from backend");
      }

      const publicKey = data.vapi_response.token;
      const assistantId = data.assistant_id;
      
      if (!vapiRef.current) {
        // Handle ES module default exports in Vite
        const VapiConstructor = (Vapi as any).default || Vapi;
        const vapi = new VapiConstructor(publicKey);
        vapiRef.current = vapi;

        vapi.on('call-start', () => {
          setIsActive(true);
          setStatus('Connected');
        });

        vapi.on('call-end', () => {
          setIsActive(false);
          setStatus('');
        });

        vapi.on('speech-start', () => {
          setStatus('Speaking...');
        });

        vapi.on('speech-end', () => {
          setStatus('Listening...');
        });

        vapi.on('error', (e: any) => {
          console.error("Vapi Error:", e);
          setIsActive(false);
          setStatus('Error connecting');
          setTimeout(() => setStatus(''), 3000);
        });
      }
      
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (err) {
        console.error("Microphone permission denied:", err);
        setStatus("Mic permission denied");
        setTimeout(() => setStatus(''), 3000);
        return;
      }

      vapiRef.current?.start(assistantId);
    } catch (e) {
      console.error("Failed to start voice call:", e);
      setStatus('Error connecting');
      setIsActive(false);
      setTimeout(() => setStatus(''), 3000);
    }
  };

  return (
    <button 
      className={`vapi-button ${isActive ? 'active' : ''}`}
      onClick={toggleCall}
      disabled={status === 'Connecting...' || status === 'Disconnecting...'}
    >
      {isActive ? '🔴 CAUSEN VOICE ACTIVE' : '🎙️ ACTIVATE CAUSEN VOICE'}
      {status && <span className="vapi-status-text">({status})</span>}
    </button>
  );
};
