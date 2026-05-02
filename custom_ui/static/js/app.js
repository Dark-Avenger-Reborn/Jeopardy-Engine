(function () {
    const RECENT_KEY = 'signalDeck.recentScans';
    const WATCH_KEY = 'signalDeck.watchlist';

    function readStorage(key, fallback) {
        try {
            const raw = localStorage.getItem(key);
            return raw ? JSON.parse(raw) : fallback;
        } catch (error) {
            return fallback;
        }
    }

    function writeStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            return;
        }
    }

    async function copyText(value) {
        if (!value) {
            return;
        }
        try {
            await navigator.clipboard.writeText(value);
        } catch (error) {
            const fallback = document.createElement('textarea');
            fallback.value = value;
            fallback.setAttribute('readonly', 'readonly');
            fallback.style.position = 'fixed';
            fallback.style.opacity = '0';
            document.body.appendChild(fallback);
            fallback.select();
            document.execCommand('copy');
            fallback.remove();
        }
    }

    function flashButton(button, text) {
        if (!button) {
            return;
        }
        const original = button.textContent;
        button.textContent = text;
        button.disabled = true;
        window.setTimeout(() => {
            button.textContent = original;
            button.disabled = false;
        }, 900);
    }

    function bootIndexPage() {
        const form = document.querySelector('[data-scan-form]');
        const presetButtons = Array.from(document.querySelectorAll('[data-preset-button]'));
        const recentContainer = document.querySelector('[data-recent-list]');
        const clearRecentButton = document.querySelector('[data-clear-recents]');
        const copyCallbackButton = document.querySelector('[data-copy-callback]');
        const recentScans = readStorage(RECENT_KEY, []);

        function getField(name) {
            return form ? form.querySelector(`[name="${name}"]`) : null;
        }

        function syncRecents() {
            if (!recentContainer) {
                return;
            }

            if (!recentScans.length) {
                recentContainer.innerHTML = '<div class="empty-copy">Nothing saved yet. Submit a scan once and this panel starts collecting your last ranges.</div>';
                return;
            }

            recentContainer.innerHTML = recentScans.map((entry) => `
                <button type="button" class="recent-entry" data-recent-entry data-linux-range="${entry.linux}" data-windows-range="${entry.windows}" data-scanner-ip="${entry.scanner}">
                    <span>
                        <strong>${entry.name}</strong>
                        <span>${entry.linux} | ${entry.windows}</span>
                    </span>
                    <span>${entry.scanner}</span>
                </button>
            `).join('');

            recentContainer.querySelectorAll('[data-recent-entry]').forEach((button) => {
                button.addEventListener('click', () => {
                    if (getField('linux_range')) {
                        getField('linux_range').value = button.dataset.linuxRange || '';
                    }
                    if (getField('windows_range')) {
                        getField('windows_range').value = button.dataset.windowsRange || '';
                    }
                    if (getField('scanner_ip')) {
                        getField('scanner_ip').value = button.dataset.scannerIp || '';
                    }
                });
            });
        }

        presetButtons.forEach((button) => {
            button.addEventListener('click', () => {
                const linuxField = getField('linux_range');
                const windowsField = getField('windows_range');
                if (linuxField) {
                    linuxField.value = button.dataset.linuxRange || linuxField.value;
                }
                if (windowsField) {
                    windowsField.value = button.dataset.windowsRange || windowsField.value;
                }
                flashButton(button, 'Loaded');
            });
        });

        if (copyCallbackButton) {
            copyCallbackButton.addEventListener('click', async () => {
                await copyText(copyCallbackButton.dataset.copyValue || '');
                flashButton(copyCallbackButton, 'Copied');
            });
        }

        if (clearRecentButton) {
            clearRecentButton.addEventListener('click', () => {
                recentScans.length = 0;
                writeStorage(RECENT_KEY, recentScans);
                syncRecents();
            });
        }

        if (form) {
            form.addEventListener('submit', () => {
                const linux = getField('linux_range')?.value.trim();
                const windows = getField('windows_range')?.value.trim();
                const scanner = getField('scanner_ip')?.value.trim();
                if (!linux || !windows || !scanner) {
                    return;
                }

                recentScans.unshift({
                    name: new Date().toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
                    linux,
                    windows,
                    scanner,
                });
                while (recentScans.length > 4) {
                    recentScans.pop();
                }
                writeStorage(RECENT_KEY, recentScans);
            });
        }

        syncRecents();
    }

    function bootGuidePage() {
        document.querySelectorAll('[data-copy-text]').forEach((button) => {
            button.addEventListener('click', async () => {
                await copyText(button.dataset.copyText || '');
                flashButton(button, 'Copied');
            });
        });
    }

    function bootResultsPage() {
        const table = document.querySelector('[data-device-table]');
        const search = document.querySelector('[data-device-search]');
        const filterButtons = Array.from(document.querySelectorAll('[data-filter]'));
        const watchlistContainer = document.querySelector('[data-watchlist]');
        const copyVisibleButton = document.querySelector('[data-copy-visible]');
        const exportJsonButton = document.querySelector('[data-export-json]');
        const exportCsvButton = document.querySelector('[data-export-csv]');
        const shellButtons = Array.from(document.querySelectorAll('[data-shell-command]'));
        const shellRows = table ? Array.from(table.querySelectorAll('[data-device-row]')) : [];
        const watchlist = new Set(readStorage(WATCH_KEY, []));
        let currentFilter = 'all';
        let socket = null;
        let term = null;

        function collectVisibleRows() {
            return shellRows.filter((row) => row.dataset.visible !== 'false');
        }

        function renderWatchlist() {
            if (!watchlistContainer) {
                return;
            }

            const pinned = shellRows
                .filter((row) => watchlist.has(row.dataset.ip || ''))
                .map((row) => row.dataset.ip);

            if (!pinned.length) {
                watchlistContainer.innerHTML = '<div class="empty-copy">Nothing pinned yet. Tap the plus icon next to a host to create a shortlist.</div>';
                return;
            }

            watchlistContainer.innerHTML = pinned.map((ip) => `
                <div class="watchlist-item">
                    <strong>${ip}</strong>
                    <button type="button" class="button tiny subtle" data-watch-remove="${ip}">Remove</button>
                </div>
            `).join('');

            watchlistContainer.querySelectorAll('[data-watch-remove]').forEach((button) => {
                button.addEventListener('click', () => {
                    watchlist.delete(button.dataset.watchRemove || '');
                    writeStorage(WATCH_KEY, Array.from(watchlist));
                    renderWatchlist();
                    syncWatchButtons();
                });
            });
        }

        function syncWatchButtons() {
            document.querySelectorAll('[data-watch-toggle]').forEach((button) => {
                const active = watchlist.has(button.dataset.watchIp || '');
                button.classList.toggle('active', active);
                button.textContent = active ? '−' : '+';
            });
        }

        function applyFilters() {
            const query = (search ? search.value : '').trim().toLowerCase();

            shellRows.forEach((row) => {
                const ip = (row.dataset.ip || '').toLowerCase();
                const os = (row.dataset.os || '').toLowerCase();
                const status = (row.dataset.status || '').toLowerCase();
                const matchesSearch = !query || ip.includes(query) || os.includes(query);
                const matchesFilter = currentFilter === 'all'
                    || (currentFilter === 'linux' && os === 'linux')
                    || (currentFilter === 'windows' && os === 'windows')
                    || (currentFilter === 'live' && status.includes('called back'))
                    || (currentFilter === 'silent' && status.includes('no response'));
                const visible = matchesSearch && matchesFilter;
                row.hidden = !visible;
                row.dataset.visible = visible ? 'true' : 'false';
            });
        }

        function sendShellCommand(command) {
            if (!socket || !term) {
                return;
            }
            socket.emit('shell_command', { cmd: `${command}\r` });
            term.focus();
        }

        if (search) {
            search.addEventListener('input', applyFilters);
        }

        filterButtons.forEach((button) => {
            button.addEventListener('click', () => {
                currentFilter = button.dataset.filter || 'all';
                filterButtons.forEach((entry) => entry.classList.toggle('active', entry === button));
                applyFilters();
            });
        });

        document.querySelectorAll('[data-watch-toggle]').forEach((button) => {
            button.addEventListener('click', () => {
                const ip = button.dataset.watchIp || '';
                if (!ip) {
                    return;
                }
                if (watchlist.has(ip)) {
                    watchlist.delete(ip);
                } else {
                    watchlist.add(ip);
                }
                writeStorage(WATCH_KEY, Array.from(watchlist));
                renderWatchlist();
                syncWatchButtons();
            });
        });

        if (copyVisibleButton) {
            copyVisibleButton.addEventListener('click', async () => {
                const ips = collectVisibleRows().map((row) => row.dataset.ip).filter(Boolean);
                await copyText(ips.join('\n'));
                flashButton(copyVisibleButton, 'Copied');
            });
        }

        if (exportJsonButton) {
            exportJsonButton.addEventListener('click', async () => {
                const payload = collectVisibleRows().map((row) => ({
                    ip: row.dataset.ip,
                    os: row.dataset.os,
                    status: row.dataset.status,
                }));
                await copyText(JSON.stringify(payload, null, 2));
                flashButton(exportJsonButton, 'Copied JSON');
            });
        }

        if (exportCsvButton) {
            exportCsvButton.addEventListener('click', async () => {
                const rows = collectVisibleRows().map((row) => `${row.dataset.ip},${row.dataset.os},${row.dataset.status}`);
                await copyText(['ip,os,status', ...rows].join('\n'));
                flashButton(exportCsvButton, 'Copied CSV');
            });
        }

        shellButtons.forEach((button) => {
            button.addEventListener('click', () => {
                sendShellCommand(button.dataset.shellCommand || '');
            });
        });

        document.querySelectorAll('[data-fill-target]').forEach((button) => {
            button.addEventListener('click', () => {
                const field = document.querySelector('#ip');
                if (field && button.dataset.fillTarget) {
                    field.value = button.dataset.fillTarget;
                }
            });
        });

        if (typeof Terminal !== 'undefined' && typeof io !== 'undefined' && document.getElementById('terminal')) {
            term = new Terminal({
                cursorBlink: true,
                fontSize: 13,
                lineHeight: 1.35,
                theme: {
                    background: '#06070a',
                    foreground: '#e8ebe7',
                    cursor: '#9ce28b',
                    selection: 'rgba(156, 226, 139, 0.24)',
                },
                rows: 22,
                cols: 92,
            });
            term.open(document.getElementById('terminal'));
            term.writeln('Signal Deck terminal ready.');
            term.writeln('Type directly, or use the shortcut cards above.');
            term.writeln('');

            socket = io();
            socket.on('connect', () => {
                term.writeln('[connected]');
                term.writeln('');
            });
            socket.on('shell_output', (data) => {
                term.write(data.output);
            });
            socket.on('disconnect', () => {
                term.writeln('\r\n[disconnected]\r\n');
            });

            term.onData((data) => {
                if (socket) {
                    socket.emit('shell_command', { cmd: data });
                }
            });
        }

        applyFilters();
        renderWatchlist();
        syncWatchButtons();
    }

    document.addEventListener('DOMContentLoaded', () => {
        const page = document.body.dataset.page || '';
        if (page === 'index') {
            bootIndexPage();
        }
        if (page === 'results') {
            bootResultsPage();
        }
        if (page === 'guide') {
            bootGuidePage();
        }
    });
})();