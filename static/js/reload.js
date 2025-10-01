/**
 * WebSocket-based live reload client
 */

(function() {
    'use strict';

    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;
    const baseReconnectDelay = 1000;
    let isNavigating = false;
    let pageLoadTime = Date.now();

    /**
     * Establishes a WebSocket connection to the live reload server.
     *
     * Attempts to connect to the live reload server. If the connection
     * fails, it will attempt to reconnect after a delay.
     */
    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        try {
            ws = new WebSocket(wsUrl);

            /**
             * Fired when the WebSocket connection is established.
             *
             * Resets the reconnect attempts counter to 0.
             */
            ws.onopen = function() {
                console.log('[markdpy] Connected to live reload server');
                reconnectAttempts = 0;
            };

        /**
         * Handle incoming messages from the live reload server.
         *
         * Messages are in JSON format with a single property 'type'.
         * If 'type' is 'reload', the page will be reloaded.
         * If 'type' is 'ping', a response with 'type' set to 'pong'
         * will be sent back to the server.
         *
         * @param {MessageEvent} event - The incoming message event.
         */
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'reload') {
                        // Don't reload if we're navigating or just loaded the page
                        const timeSinceLoad = Date.now() - pageLoadTime;
                        if (isNavigating) {
                            console.log('[markdpy] Ignoring reload during navigation');
                            return;
                        }
                        if (timeSinceLoad < 500) {
                            console.log('[markdpy] Ignoring reload shortly after page load');
                            return;
                        }
                        
                        console.log('[markdpy] Reloading page...');
                        // Small delay to avoid interfering with navigation
                        setTimeout(function() {
                            window.location.reload();
                        }, 100);
                    } else if (data.type === 'ping') {
                        // Respond to ping with pong
                        ws.send(JSON.stringify({ type: 'pong' }));
                    }
                } catch (e) {
                    console.error('[markdpy] Error parsing message:', e);
                }
            };

            /**
             * Fired when the WebSocket connection is closed.
             *
             * Logs a message to the console indicating that the connection has been closed and
             * attempts to reconnect to the live reload server.
             */
            ws.onclose = function() {
                console.log('[markdpy] Disconnected from live reload server');
                // Don't try to reconnect if page is being unloaded
                if (!document.hidden) {
                    attemptReconnect();
                }
            };


            /**
             * Fired when a WebSocket error occurs.
             *
             * Logs a message to the console indicating that a WebSocket error has occurred and
             * closes the WebSocket connection.
             *
             * @param {Error} error - The WebSocket error that occurred.
             */
            ws.onerror = function(error) {
                console.error('[markdpy] WebSocket error:', error);
                ws.close();
            };

        } catch (e) {
            console.error('[markdpy] Failed to create WebSocket:', e);
            attemptReconnect();
        }
    }

    /**
     * Attempts to reconnect to the live reload server.
     *
     * If the maximum reconnect attempts have been reached, logs a message to the console
     * indicating that live reload has been disabled.
     *
     * Otherwise, calculates the exponential backoff delay, increments the reconnect attempts
     * counter, and logs a message to the console indicating the reconnect attempt.
     *
     * The reconnect attempt is scheduled using setTimeout.
     */
    function attemptReconnect() {
        if (reconnectAttempts >= maxReconnectAttempts) {
            console.log('[markdpy] Max reconnect attempts reached. Live reload disabled.');
            return;
        }

        const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts);
        reconnectAttempts++;

        console.log(`[markdpy] Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`);
        
        setTimeout(connect, delay);
    }

    // Start connection when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', connect);
    } else {
        connect();
    }

    // Clean up WebSocket connection before page unload
    window.addEventListener('beforeunload', function() {
        console.log('[markdpy] Page unloading, closing WebSocket');
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
    });

    // Debug: Log when navigation is attempted
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'A' || e.target.closest('a')) {
            const link = e.target.tagName === 'A' ? e.target : e.target.closest('a');
            console.log('[markdpy] Link clicked:', link.href);
            isNavigating = true;
        }
    }, true);

})();
