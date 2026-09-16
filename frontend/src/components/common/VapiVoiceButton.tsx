import React, { useState, useRef, useEffect } from 'react';
import Vapi from '@vapi-ai/web';
import { API_BASE_URL } from '../../config';
import { VoiceCommandService } from '../../services/voice/VoiceCommandService';
import styles from './VapiVoiceButton.module.css';

export const VapiVoiceButton: React.FC = () => {
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
      const response = await fetch(`${API_BASE_URL}/api/vapi/token`);
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

        vapi.on('message', (message: any) => {
          if (message.type === 'tool-calls') {
            const toolWithToolCallList = message.toolWithToolCallList || [];
            
            toolWithToolCallList.forEach((toolCallWrapper: any) => {
              const call = toolCallWrapper.toolCall;
              
              let args = {};
              try {
                args = typeof call.function.arguments === 'string' 
                       ? JSON.parse(call.function.arguments) 
                       : call.function.arguments;
              } catch (e) {
                console.error("Failed to parse tool call arguments", e);
              }

              const validationResult = VoiceCommandService.parseAndValidate(args);
              let resultToReturn;
              
              if (validationResult.success && validationResult.command) {
                resultToReturn = VoiceCommandService.handleCommand(validationResult.command);
              } else {
                resultToReturn = {
                  success: false,
                  error: validationResult.error
                };
              }

              // Send the result back to Vapi
              if (vapiRef.current) {
                try {
                  vapiRef.current.send({
                    type: 'add-message',
                    message: {
                      role: 'tool',
                      tool_call_id: call.id,
                      name: call.function.name,
                      content: JSON.stringify(resultToReturn)
                    }
                  });
                } catch (err) {
                  console.error("Failed to send tool response to Vapi", err);
                }
              }
            });
          }
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
      className={`${styles.button} ${isActive ? styles.active : ''}`}
      onClick={toggleCall}
      disabled={status === 'Connecting...' || status === 'Disconnecting...'}
    >
      {isActive ? '🔴 CAUSEN VOICE ACTIVE' : '🎙️ ACTIVATE CAUSEN VOICE'}
      {status && <span className={styles.statusText}>({status})</span>}
    </button>
  );
};
