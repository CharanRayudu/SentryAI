import { useEffect, useRef, useState, useCallback } from 'react';

type WebSocketMessage = {
    type: string;
    [key: string]: any;
};

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;

export function useAgentSocket(url: string = 'ws://localhost:8000/api/v1/ws/mission') {
    const socketRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
    const [connectionError, setConnectionError] = useState<string | null>(null);

    useEffect(() => {
        // Only connect on client side
        if (typeof window === 'undefined') return;
        
        const connect = () => {
            // Don't reconnect if we've exceeded max attempts
            if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
                setConnectionError(`Unable to connect after ${MAX_RECONNECT_ATTEMPTS} attempts. Backend may be offline.`);
                return;
            }
            
            try {
                const ws = new WebSocket(url);

                ws.onopen = () => {
                    console.log('Agent Socket Connected');
                    setIsConnected(true);
                    setConnectionError(null);
                    reconnectAttemptsRef.current = 0; // Reset on successful connection
                };

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        setLastMessage(data);
                    } catch (e) {
                        console.error('Failed to parse WebSocket message:', e);
                    }
                };

                ws.onerror = () => {
                    // Error is handled in onclose
                };

                ws.onclose = () => {
                    setIsConnected(false);
                    socketRef.current = null;
                    
                    reconnectAttemptsRef.current++;
                    
                    if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
                        console.log(`Agent Socket Disconnected. Retry ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS}...`);
                        reconnectTimeoutRef.current = setTimeout(connect, RECONNECT_DELAY);
                    } else {
                        console.log('Agent Socket: Max reconnection attempts reached. Backend may be offline.');
                        setConnectionError('Unable to connect to backend. Please check if the API server is running.');
                    }
                };

                socketRef.current = ws;
            } catch (e) {
                console.error('WebSocket connection error:', e);
                setConnectionError('Failed to create WebSocket connection');
            }
        };

        connect();

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            socketRef.current?.close();
        };
    }, [url]);

    const sendMessage = useCallback((type: string, payload: any) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type, ...payload }));
        } else {
            console.warn('Socket not connected');
        }
    }, []);

    const stopMission = useCallback((missionId?: string, runId?: string) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
                type: 'client:stop',
                mission_id: missionId,
                run_id: runId
            }));
        } else {
            console.warn('Socket not connected');
        }
    }, []);
    
    const reconnect = useCallback(() => {
        reconnectAttemptsRef.current = 0;
        setConnectionError(null);
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        socketRef.current?.close();
    }, []);

    return { isConnected, lastMessage, sendMessage, stopMission, connectionError, reconnect };
}
