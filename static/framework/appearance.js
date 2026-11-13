(() => {
  if (window.yunaAppearance) return;
  window.yunaAppearance = { version: '2026-11' };
  document.body.classList.add('yuna-app');
  const controls = "<div class=\"appearance-controls\"><label class=\"skin-picker\"><i data-lucide=\"palette\" aria-hidden=\"true\"></i><span>明暗</span><select data-theme-select aria-label=\"选择显示模式\"><option value=\"system\">跟随系统</option><option value=\"light\">浅色</option><option value=\"dark\">深色</option></select></label><label class=\"skin-picker skin-picker--style\"><i data-lucide=\"swatch-book\" aria-hidden=\"true\"></i><span>皮肤</span><select data-skin-select aria-label=\"选择视觉皮肤\"><option value=\"102\">102</option><option value=\"arknights\">明日方舟</option><option value=\"scarlet\">红魔馆</option></select></label></div>";
  document.querySelectorAll('[data-appearance-controls]').forEach(host => { host.innerHTML = controls; });
  document.querySelectorAll('[data-theme-toggle]').forEach(button => { button.outerHTML = controls; });
  const skinModes = ['102', 'arknights', 'scarlet'];
  const applySkin = (value, persist = true) => {
    const skin = skinModes.includes(value) ? value : '102';
    document.documentElement.dataset.skin = skin;
    document.querySelectorAll('[data-skin-select]').forEach(select => { select.value = skin; });
    if (persist) { try { localStorage.setItem('yuna-skin', skin); } catch {} }
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', getComputedStyle(document.documentElement).getPropertyValue('--bg').trim());
    document.dispatchEvent(new CustomEvent('appearancechange'));
  };
  applySkin(document.documentElement.dataset.skin, false);
  document.querySelectorAll('[data-skin-select]').forEach(select => {
    select.addEventListener('change', () => applySkin(select.value));
  });
  addEventListener('storage', event => { if (event.key === 'yuna-skin') applySkin(event.newValue, false); });

  const themeModes = ['system', 'light', 'dark'];
  const themeDetails = {
    system: { label: '跟随系统', icon: 'monitor' },
    light: { label: '浅色模式', icon: 'sun' },
    dark: { label: '夜间模式', icon: 'moon-star' }
  };
  const systemTheme = matchMedia('(prefers-color-scheme: dark)');
  const readSharedTheme = () => document.cookie.match(/(?:^|; )yuna-theme=(light|dark)/)?.[1];
  const themeStorage = {
    get: () => { try { return localStorage.getItem('yuna-theme'); } catch { return null; } },
    set: value => { try { localStorage.setItem('yuna-theme', value); } catch {} },
    clear: () => { try { localStorage.removeItem('yuna-theme'); } catch {} }
  };
  const sharedTheme = readSharedTheme();
  let themeMode = sharedTheme || themeStorage.get() || 'system';
  if (!themeModes.includes(themeMode)) themeMode = 'system';

  const writeSharedTheme = mode => {
    if (!/(^|\.)102\.yuna\.team$/.test(location.hostname)) return;
    if (mode === 'system') {
      document.cookie = 'yuna-theme=; Max-Age=0; Path=/; Domain=.102.yuna.team; Secure; SameSite=Lax';
    } else {
      document.cookie = `yuna-theme=${mode}; Max-Age=31536000; Path=/; Domain=.102.yuna.team; Secure; SameSite=Lax`;
    }
  };

  const renderTheme = () => {
    const detail = themeDetails[themeMode];
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.innerHTML = `<i data-lucide="${detail.icon}"></i><span>${detail.label}</span>`;
      button.setAttribute('aria-label', `显示主题：${detail.label}。点击切换`);
      button.title = `当前：${detail.label}`;
    });
    document.querySelectorAll('[data-theme-select]').forEach(select => { select.value = themeMode; });
    const dark = themeMode === 'dark' || (themeMode === 'system' && systemTheme.matches);
    document.documentElement.dataset.bsTheme = dark ? 'dark' : 'light';
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', getComputedStyle(document.documentElement).getPropertyValue('--bg').trim());
    document.dispatchEvent(new CustomEvent('appearancechange'));
    if (window.lucide) window.lucide.createIcons();
  };

  const applyTheme = mode => {
    themeMode = mode;
    if (mode === 'system') {
      document.documentElement.removeAttribute('data-theme');
      themeStorage.clear();
    } else {
      document.documentElement.dataset.theme = mode;
      themeStorage.set(mode);
    }
    writeSharedTheme(mode);
    renderTheme();
  };

  document.querySelectorAll('[data-theme-toggle]').forEach(button => {
    button.addEventListener('click', () => {
      const next = themeModes[(themeModes.indexOf(themeMode) + 1) % themeModes.length];
      applyTheme(next);
    });
  });
  document.querySelectorAll('[data-theme-select]').forEach(select => {
    select.addEventListener('change', () => { if (themeModes.includes(select.value)) applyTheme(select.value); });
  });
  systemTheme.addEventListener('change', () => { if (themeMode === 'system') renderTheme(); });
  addEventListener('storage', event => {
    if (event.key !== 'yuna-theme') return;
    const next = event.newValue === 'light' || event.newValue === 'dark' ? event.newValue : 'system';
    themeMode = next;
    if (next === 'system') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.dataset.theme = next;
    renderTheme();
  });
  const syncSharedTheme = () => {
    const next = readSharedTheme() || (/(^|\.)102\.yuna\.team$/.test(location.hostname) ? 'system' : themeStorage.get() || 'system');
    if (next === themeMode) return;
    themeMode = next;
    if (next === 'system') {
      document.documentElement.removeAttribute('data-theme');
      themeStorage.clear();
    } else {
      document.documentElement.dataset.theme = next;
      themeStorage.set(next);
    }
    renderTheme();
  };
  addEventListener('focus', syncSharedTheme);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) syncSharedTheme(); });
  writeSharedTheme(themeMode);
  renderTheme();

  // Enhance native selects only after the shared appearance state is ready.
  document.querySelectorAll('[data-theme-select],[data-skin-select]').forEach((select, index) => {
    let root = select.closest('.skin-picker');
    if (root.tagName === 'LABEL') {
      const wrapper = document.createElement('div');
      wrapper.className = root.className;
      wrapper.append(...root.childNodes);
      root.replaceWith(wrapper);
      root = wrapper;
    }
    root.classList.add('picker-enhanced');
    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'appearance-trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    const name = select.hasAttribute('data-skin-select') ? '皮肤' : '明暗';
    trigger.innerHTML = `<i data-lucide="${name === '皮肤' ? 'swatch-book' : 'palette'}" aria-hidden="true"></i><span class="appearance-label">${name}</span><span class="appearance-value"></span><i data-lucide="chevron-down" aria-hidden="true"></i>`;
    const menu = document.createElement('div');
    menu.className = 'appearance-menu';
    menu.id = `appearance-menu-${index}`;
    menu.hidden = true;
    menu.setAttribute('role', 'listbox');
    menu.setAttribute('aria-label', select.getAttribute('aria-label'));
    trigger.setAttribute('aria-controls', menu.id);
    const options = [...select.options].map(option => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'appearance-option';
      button.setAttribute('role', 'option');
      button.tabIndex = -1;
      const text = document.createElement('span');
      text.textContent = option.textContent;
      const check = document.createElement('span');
      check.className = 'appearance-check';
      check.textContent = '✓';
      check.setAttribute('aria-hidden', 'true');
      button.append(text, check);
      button.addEventListener('click', () => {
        select.value = option.value;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        close(true);
      });
      menu.appendChild(button);
      return button;
    });
    const refresh = () => {
      trigger.querySelector('.appearance-value').textContent = select.selectedOptions[0].textContent;
      trigger.setAttribute('aria-label', `${select.getAttribute('aria-label')}：${select.selectedOptions[0].textContent}`);
      options.forEach((option, i) => option.setAttribute('aria-selected', String(select.options[i].value === select.value)));
    };
    const close = (restoreFocus = false) => {
      menu.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
      if (restoreFocus) trigger.focus();
    };
    const open = () => {
      menu.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      options[select.selectedIndex].focus();
    };
    trigger.addEventListener('click', () => menu.hidden ? open() : close(true));
    root.addEventListener('keydown', event => {
      const current = options.indexOf(document.activeElement);
      if (event.key === 'Escape' && !menu.hidden) { event.preventDefault(); close(true); }
      if (event.key === 'Tab' && !menu.hidden) close(current >= 0);
      if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
        event.preventDefault();
        if (menu.hidden) open();
        else {
          const target = event.key === 'Home' ? 0 : event.key === 'End' ? options.length - 1 : (current + (event.key === 'ArrowDown' ? 1 : -1) + options.length) % options.length;
          options[target].focus();
        }
      }
    });
    root.addEventListener('focusout', event => { if (!root.contains(event.relatedTarget)) close(); });
    document.addEventListener('pointerdown', event => { if (!root.contains(event.target)) close(); });
    select.addEventListener('change', refresh);
    document.addEventListener('appearancechange', refresh);
    select.hidden = true;
    root.append(trigger, menu);
    refresh();
  });
  if (window.lucide) window.lucide.createIcons();



})();
