// The UI depends on this small adapter, so cloud sync can replace it later.
window.taskStore = {
  key(date) { return 'daily-tasks:v1:' + date; },
  load(date) {
    try {
      const raw = localStorage.getItem(this.key(date));
      if (raw !== null) {
        const data = JSON.parse(raw);
        return Array.isArray(data) ? data.filter(x => typeof x.text === 'string' && typeof x.done === 'boolean') : [];
      }
    } catch (_) { /* Storage can be unavailable in private browsing. */ }
    return [
      {text:'AI 编程 15 分钟',done:false},
      {text:'阅读今日 AI 科技报',done:false},
      {text:'查看杭州工作雷达',done:false}
    ];
  },
  save(date,tasks) { localStorage.setItem(this.key(date),JSON.stringify(tasks)); }
};
