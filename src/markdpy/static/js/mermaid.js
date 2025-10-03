/**
 * Mermaid Diagram Initialization for markdpy
 * Configures and initializes Mermaid.js for rendering diagrams in markdown
 */

(function() {
    'use strict';

    /**
     * Get current theme for Mermaid styling
     */
    function getMermaidTheme() {
        const theme = document.documentElement.getAttribute('data-theme') || 'light';
        return theme === 'dark' ? 'dark' : 'default';
    }

    /**
     * Initialize Mermaid with configuration
     */
    function initMermaid() {
        // Check if Mermaid is loaded
        if (typeof mermaid === 'undefined') {
            console.log('[markdpy] Mermaid.js not loaded, skipping diagram initialization');
            return;
        }

        try {
            // Configure Mermaid
            mermaid.initialize({
                startOnLoad: true,
                theme: getMermaidTheme(),
                securityLevel: 'loose',
                themeVariables: {
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                },
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                },
                sequence: {
                    useMaxWidth: true,
                    diagramMarginX: 50,
                    diagramMarginY: 10,
                    actorMargin: 50,
                    boxMargin: 10,
                    boxTextMargin: 5,
                    noteMargin: 10,
                    messageMargin: 35
                },
                gantt: {
                    useMaxWidth: true,
                    barHeight: 20,
                    barGap: 4,
                    topPadding: 50,
                    leftPadding: 75,
                    gridLineStartPadding: 35,
                    fontSize: 11,
                    numberSectionStyles: 4,
                    axisFormat: '%Y-%m-%d'
                }
            });

            console.log('[markdpy] Mermaid.js initialized with theme:', getMermaidTheme());

            // Re-render diagrams when theme changes
            observeThemeChanges();

        } catch (error) {
            console.error('[markdpy] Error initializing Mermaid:', error);
        }
    }

    /**
     * Re-render Mermaid diagrams
     */
    function rerenderDiagrams() {
        if (typeof mermaid === 'undefined') return;

        try {
            // Update theme configuration
            mermaid.initialize({
                theme: getMermaidTheme()
            });

            // Find all mermaid code blocks
            const diagrams = document.querySelectorAll('.language-mermaid, code.language-mermaid');
            
            diagrams.forEach((diagram, index) => {
                const parent = diagram.parentElement;
                const code = diagram.textContent;
                
                // Create a new div for the diagram
                const div = document.createElement('div');
                div.className = 'mermaid';
                div.setAttribute('data-processed', 'false');
                div.textContent = code;
                
                // Replace the code block with the diagram div
                if (parent && parent.tagName === 'PRE') {
                    parent.replaceWith(div);
                } else {
                    diagram.replaceWith(div);
                }
            });

            // Render the diagrams
            mermaid.init(undefined, document.querySelectorAll('.mermaid[data-processed="false"]'));
            
            console.log('[markdpy] Mermaid diagrams re-rendered');

        } catch (error) {
            console.error('[markdpy] Error re-rendering Mermaid diagrams:', error);
        }
    }

    /**
     * Observe theme changes and re-render diagrams
     */
    function observeThemeChanges() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                    console.log('[markdpy] Theme changed, re-rendering Mermaid diagrams');
                    rerenderDiagrams();
                }
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme']
        });
    }

    /**
     * Initialize on page load
     */
    function init() {
        // Wait for Mermaid to be loaded (if using CDN)
        if (typeof mermaid !== 'undefined') {
            initMermaid();
        } else {
            // Poll for Mermaid availability
            let attempts = 0;
            const maxAttempts = 20; // 2 seconds max wait
            const checkInterval = setInterval(() => {
                attempts++;
                if (typeof mermaid !== 'undefined') {
                    clearInterval(checkInterval);
                    initMermaid();
                } else if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    console.log('[markdpy] Mermaid.js not loaded after waiting');
                }
            }, 100);
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export for programmatic access
    window.markdpyMermaid = {
        initMermaid,
        rerenderDiagrams,
        getMermaidTheme
    };
})();
