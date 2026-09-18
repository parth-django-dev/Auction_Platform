import { useState, useEffect, useRef, useCallback } from 'react';

export function useAuctionSocket(itemId, { onBidUpdate, onError, onAuctionEnded } = {}) {
  const [status, setStatus] = useState('disconnected'); // 'connecting' | 'connected' | 'disconnected' | 'error'
  const [lastError, setLastError] = useState(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isUnmountedRef = useRef(false);

  // Keep callback refs updated without re-triggering connect
  const onBidUpdateRef = useRef(onBidUpdate);
  const onErrorRef = useRef(onError);
  const onAuctionEndedRef = useRef(onAuctionEnded);

  useEffect(() => {
    onBidUpdateRef.current = onBidUpdate;
    onErrorRef.current = onError;
    onAuctionEndedRef.current = onAuctionEnded;
  }, [onBidUpdate, onError, onAuctionEnded]);

  const connect = useCallback(() => {
    if (!itemId) return;

    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    setStatus('connecting');
    setLastError(null);

    // Build WebSocket URL matching current origin (Vite dev server proxies /ws to Daphne)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/auction/${itemId}/`;

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        if (isUnmountedRef.current) {
          ws.close();
          return;
        }
        setStatus('connected');
        setLastError(null);
      };

      ws.onmessage = (event) => {
        if (isUnmountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'bid_update') {
            onBidUpdateRef.current?.(data);
          } else if (data.type === 'auction_ended') {
            onAuctionEndedRef.current?.(data);
          } else if (data.type === 'error') {
            setLastError(data.message);
            onErrorRef.current?.(data.message);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (err) => {
        if (isUnmountedRef.current) return;
        console.warn('WebSocket encountered error:', err);
        setStatus('error');
      };

      ws.onclose = (event) => {
        if (isUnmountedRef.current) return;
        setStatus('disconnected');
        
        // Auto-reconnect after 3 seconds if closed cleanly or unexpectedly
        if (!event.wasClean) {
          reconnectTimeoutRef.current = setTimeout(() => {
            if (!isUnmountedRef.current) {
              connect();
            }
          }, 3000);
        }
      };
    } catch (err) {
      setStatus('error');
      setLastError(err.message);
    }
  }, [itemId]);

  useEffect(() => {
    isUnmountedRef.current = false;
    connect();

    return () => {
      isUnmountedRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      const ws = socketRef.current;
      if (ws) {
        // Detach handlers so no error logs fire during intentional unmount
        ws.onerror = null;
        ws.onclose = null;
        ws.onmessage = null;

        // If socket is still connecting, waiting for onopen before calling close
        // prevents Chromium from logging "WebSocket is closed before the connection is established"
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => {
            try {
              ws.close();
            } catch (e) {
              // ignore
            }
          };
        } else if (ws.readyState === WebSocket.OPEN) {
          try {
            ws.close();
          } catch (e) {
            // ignore
          }
        }
        socketRef.current = null;
      }
    };
  }, [connect]);

  const sendBid = useCallback((amount) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      const msg = 'Not connected to auction server.';
      setLastError(msg);
      onErrorRef.current?.(msg);
      return false;
    }

    try {
      socketRef.current.send(JSON.stringify({
        type: 'bid',
        amount: Number(amount),
      }));
      setLastError(null);
      return true;
    } catch (err) {
      setLastError(err.message);
      onErrorRef.current?.(err.message);
      return false;
    }
  }, []);

  return {
    status,
    isConnected: status === 'connected',
    lastError,
    clearError: () => setLastError(null),
    sendBid,
    reconnect: connect,
  };
}
