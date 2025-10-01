/**
 * Theme Switcher for markdpy
 * Handles theme toggle button, localStorage persistence, and CSS variable updates
 */

(function() {
    'use strict';

    // Theme configuration
    const THEMES = ['light', 'dark'];
    const STORAGE_KEY = 'markdpy-theme';
    const DEFAULT_THEME = 'light';

    /**
     * Get current theme from localStorage or default
     */
    function getCurrentTheme() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored && THEMES.includes(stored)) {
            return stored;
        }
        // Check system preference if no stored theme
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return DEFAULT_THEME;
    }

    /**
     * Apply theme by updating the theme stylesheet link
     */
    function applyTheme(theme) {
        const themeLink = document.getElementById('theme-stylesheet');
        if (themeLink) {
            themeLink.href = `/static/css/themes/${theme}.css`;
        }

        // Update data attribute on html element for CSS targeting
        document.documentElement.setAttribute('data-theme', theme);

        // Update button text/icon if it exists
        updateThemeButton(theme);

        // Store preference
        localStorage.setItem(STORAGE_KEY, theme);

        console.log(`[markdpy] Theme applied: ${theme}`);
    }

    /**
     * Update theme toggle button state
     */
    function updateThemeButton(theme) {
        const button = document.getElementById('theme-toggle');
        if (!button) return;

        const label = theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode';

        button.setAttribute('aria-label', label);
        button.setAttribute('title', label);
        button.setAttribute('data-theme', theme);
        button.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
    }

    /**
     * Toggle between light and dark themes
     */
    function toggleTheme() {
        const current = getCurrentTheme();
        const next = current === 'light' ? 'dark' : 'light';
        applyTheme(next);
    }

    /**
     * Create theme toggle button if it doesn't exist
     */
    function createThemeButton() {
        // Check if button already exists
        if (document.getElementById('theme-toggle')) {
            return;
        }

        const button = document.createElement('button');
        button.id = 'theme-toggle';
        button.className = 'theme-toggle';
        button.setAttribute('type', 'button');
        button.setAttribute('role', 'switch');
        button.setAttribute('aria-label', 'Toggle theme');

        // Add icon spans
        const sunIcon = document.createElement('span');
        sunIcon.className = 'theme-toggle-icon sun';
        sunIcon.textContent = '🌞';
        sunIcon.setAttribute('aria-hidden', 'true');

        const moonIcon = document.createElement('span');
        moonIcon.className = 'theme-toggle-icon moon';
        moonIcon.textContent = '🌚';
        moonIcon.setAttribute('aria-hidden', 'true');

        button.appendChild(sunIcon);
        button.appendChild(moonIcon);

        // Add click handler
        button.addEventListener('click', toggleTheme);

        // Insert button into header or body
        const header = document.querySelector('header') || document.querySelector('.header');
        if (header) {
            header.appendChild(button);
        } else {
            // Fallback: add to body as fixed position
            document.body.appendChild(button);
        }

        // Initialize button state with current theme
        const currentTheme = getCurrentTheme();
        updateThemeButton(currentTheme);

        console.log('[markdpy] Theme toggle button created');
    }

    /**
     * Initialize theme system
     */
    function init() {
        // Apply theme immediately to avoid flash
        const theme = getCurrentTheme();
        applyTheme(theme);

        // Create toggle button
        createThemeButton();

        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                // Only apply system preference if user hasn't manually set a theme
                if (!localStorage.getItem(STORAGE_KEY)) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    applyTheme(newTheme);
                }
            });
        }

        console.log('[markdpy] Theme system initialized');
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export for programmatic access
    window.markdpyTheme = {
        getCurrentTheme,
        applyTheme,
        toggleTheme,
        THEMES
    };
})();
