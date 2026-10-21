import { useEffect, useRef, useState, useCallback } from "react";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

const VIEWPORT = { width: 1280, height: 800 };

export default function BrowserView({ taskId, interactive = true }) {
  const [connected, setConnected] = useState(false);
  const [frame, setFrame] = useState(null);
  const wsRef = useRef(null);
  const imgRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/browser/${taskId}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "frame") {
        setFrame(msg.data);
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [taskId]);

  const scaleCoordinates = useCallback((clientX, clientY) => {
    const img = imgRef.current;
    if (!img) return null;

    const rect = img.getBoundingClientRect();
    const scaleX = VIEWPORT.width / rect.width;
    const scaleY = VIEWPORT.height / rect.height;

    return {
      x: Math.round((clientX - rect.left) * scaleX),
      y: Math.round((clientY - rect.top) * scaleY),
    };
  }, []);

  function send(msg) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }

  function handleMouseDown(e) {
    if (!interactive) return;
    const coords = scaleCoordinates(e.clientX, e.clientY);
    if (coords) {
      send({ type: "mousedown", x: coords.x, y: coords.y, button: e.button });
    }
  }

  function handleMouseUp(e) {
    if (!interactive) return;
    const coords = scaleCoordinates(e.clientX, e.clientY);
    if (coords) {
      send({ type: "mouseup", x: coords.x, y: coords.y, button: e.button });
    }
  }

  function handleMouseMove(e) {
    if (!interactive) return;
    const coords = scaleCoordinates(e.clientX, e.clientY);
    if (coords) {
      send({ type: "mousemove", x: coords.x, y: coords.y });
    }
  }

  function handleKeyDown(e) {
    if (!interactive) return;
    e.preventDefault();
    send({ type: "keydown", key: e.key, code: e.code, modifiers: getModifiers(e) });
  }

  function handleKeyUp(e) {
    if (!interactive) return;
    e.preventDefault();
    send({ type: "keyup", key: e.key, code: e.code, modifiers: getModifiers(e) });
  }

  function handleWheel(e) {
    if (!interactive) return;
    e.preventDefault();
    const coords = scaleCoordinates(e.clientX, e.clientY);
    if (coords) {
      send({ type: "scroll", x: coords.x, y: coords.y, deltaX: e.deltaX, deltaY: e.deltaY });
    }
  }

  function getModifiers(e) {
    const mods = [];
    if (e.altKey) mods.push("Alt");
    if (e.ctrlKey) mods.push("Control");
    if (e.metaKey) mods.push("Meta");
    if (e.shiftKey) mods.push("Shift");
    return mods;
  }

  return (
    <div
      ref={containerRef}
      className="relative bg-black rounded-lg overflow-hidden select-none"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onKeyUp={handleKeyUp}
    >
      {!connected && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 text-white z-10">
          Connecting to browser...
        </div>
      )}

      {connected && !frame && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 text-white z-10">
          Loading page...
        </div>
      )}

      {frame ? (
        <img
          ref={imgRef}
          src={`data:image/jpeg;base64,${frame}`}
          alt="Browser view"
          className="w-full h-auto"
          style={{ imageRendering: "auto", cursor: interactive ? "default" : "not-allowed" }}
          draggable={false}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseMove={handleMouseMove}
          onWheel={handleWheel}
          onContextMenu={(e) => e.preventDefault()}
        />
      ) : (
        <div className="w-full" style={{ aspectRatio: `${VIEWPORT.width}/${VIEWPORT.height}` }} />
      )}
    </div>
  );
}
