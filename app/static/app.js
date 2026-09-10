/**
 * AegisShield — Intelligent Fraud Detection Platform Front-End Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // Global state
  let currentTxnId = null;
  let presetsData = {};

  // DOM Elements
  const tabs = document.querySelectorAll('.nav-tab');
  const tabPanels = document.querySelectorAll('.tab-panel');

  const evalForm = document.getElementById('form-evaluate');
  const btnReset = document.getElementById('btn-reset-form');
  const resTxnId = document.getElementById('res-txn-id');
  const badgeDecision = document.getElementById('badge-decision');
  const decisionText = document.getElementById('decision-text');
  const decisionIcon = document.getElementById('decision-icon');
  const resRiskTier = document.getElementById('res-risk-tier');
  const resLatency = document.getElementById('res-latency');
  const resModelVer = document.getElementById('res-model-ver');
  const resScoreNum = document.getElementById('res-score-number');
  const gaugeBar = document.getElementById('gauge-bar');

  // Factor breakdown elements
  const valRuleScore = document.getElementById('val-rule-score');
  const valMlProb = document.getElementById('val-ml-prob');
  const valIsoScore = document.getElementById('val-iso-score');
  const valBehScore = document.getElementById('val-beh-score');
  const barRule = document.getElementById('bar-rule');
  const barMl = document.getElementById('bar-ml');
  const barIso = document.getElementById('bar-iso');
  const barBeh = document.getElementById('bar-beh');

  const reasonsList = document.getElementById('reasons-list');
  const contribBars = document.getElementById('contrib-bars-list');

  // Quick actions
  const btnQuickFraud = document.getElementById('btn-quick-fraud');
  const btnQuickLegit = document.getElementById('btn-quick-legit');

  // Tables
  const tbodyAlerts = document.getElementById('tbody-alerts');
  const tbodyRecent = document.getElementById('tbody-recent');
  const tbodyBenchmarks = document.getElementById('tbody-benchmarks');
  const featImportanceBars = document.getElementById('feature-importance-bars');
  const badgeAlertsCount = document.getElementById('badge-alerts-count');

  // -------------------------------------------------------------------------
  // 1. Tab Navigation
  // -------------------------------------------------------------------------
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPanel = document.getElementById(tab.dataset.tab);
      if (targetPanel) {
        targetPanel.classList.add('active');
      }

      // Tab specific load actions
      if (tab.dataset.tab === 'tab-alerts') {
        loadAlerts();
        loadRecentTransactions();
      } else if (tab.dataset.tab === 'tab-benchmarks') {
        loadBenchmarks();
      }
    });
  });

  // -------------------------------------------------------------------------
  // 2. Presets Loading & Pre-filling
  // -------------------------------------------------------------------------
  async function loadPresets() {
    try {
      const res = await fetch('/api/presets');
      if (res.ok) {
        const presets = await res.json();
        presets.forEach(p => {
          presetsData[p.id] = p.payload;
        });
      }
    } catch (e) {
      console.warn('Could not load presets from API, using client fallback', e);
    }
  }

  const presetChips = document.querySelectorAll('.chip[data-preset]');
  presetChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const pId = chip.dataset.preset;
      applyPreset(pId);
    });
  });

  function applyPreset(pId) {
    const p = presetsData[pId];
    if (!p) return;

    document.getElementById('inp-amount').value = p.amount || 100.0;
    document.getElementById('inp-dist').value = p.distance_from_home || 0.0;
    document.getElementById('inp-txn-type').value = p.transaction_type || 'PURCHASE';
    document.getElementById('inp-pay-method').value = p.payment_method || 'UPI';
    document.getElementById('inp-merch-cat').value = p.merchant_category || 'ONLINE_RETAIL';
    document.getElementById('inp-customer-avg').value = p.customer_avg_amount_30d || 500.0;
    document.getElementById('inp-velocity-1h').value = p.customer_txn_count_last_1h || 1;
    document.getElementById('inp-failed-24h').value = p.failed_attempts_last_24h || 0;
    document.getElementById('chk-new-device').checked = !!p.is_new_device;
    document.getElementById('chk-vpn').checked = !!p.is_vpn_proxy;
    document.getElementById('chk-new-beneficiary').checked = !!p.is_new_beneficiary;

    showToast(`Loaded scenario: ${chipName(pId)}`, 'success');

    // Auto trigger evaluation
    evalForm.dispatchEvent(new Event('submit'));
  }

  function chipName(id) {
    const el = document.querySelector(`.chip[data-preset="${id}"]`);
    return el ? el.innerText : id;
  }

  btnReset.addEventListener('click', () => {
    evalForm.reset();
    document.getElementById('inp-amount').value = '4800.00';
    document.getElementById('inp-dist').value = '1350.0';
    document.getElementById('inp-customer-avg').value = '650.0';
  });

  // -------------------------------------------------------------------------
  // 3. Evaluation Form Handler
  // -------------------------------------------------------------------------
  evalForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
      amount: parseFloat(document.getElementById('inp-amount').value),
      distance_from_home: parseFloat(document.getElementById('inp-dist').value),
      transaction_type: document.getElementById('inp-txn-type').value,
      payment_method: document.getElementById('inp-pay-method').value,
      merchant_category: document.getElementById('inp-merch-cat').value,
      customer_avg_amount_30d: parseFloat(document.getElementById('inp-customer-avg').value),
      customer_txn_count_last_1h: parseInt(document.getElementById('inp-velocity-1h').value, 10),
      failed_attempts_last_24h: parseInt(document.getElementById('inp-failed-24h').value, 10),
      is_new_device: document.getElementById('chk-new-device').checked,
      is_vpn_proxy: document.getElementById('chk-vpn').checked,
      is_new_beneficiary: document.getElementById('chk-new-beneficiary').checked,
    };

    const submitBtn = document.getElementById('btn-submit-eval');
    submitBtn.classList.add('loading');

    try {
      const res = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Inference error: HTTP ${res.status}`);
      }

      const data = await res.json();
      renderEvaluationResult(data);
    } catch (err) {
      showToast(err.message, 'danger');
    } finally {
      submitBtn.classList.remove('loading');
    }
  });

  function renderEvaluationResult(data) {
    currentTxnId = data.transaction_id;
    resTxnId.innerText = `ID: ${data.transaction_id}`;

    const score = data.risk_score;
    animateGauge(score);

    // Decision badge style & text
    badgeDecision.className = 'decision-badge';
    let icon = '✓';
    let decisionClass = 'badge-allow';

    if (data.decision === 'BLOCK') {
      decisionClass = 'badge-block';
      icon = '✕';
    } else if (data.decision === 'MANUAL_REVIEW') {
      decisionClass = 'badge-review';
      icon = '👁';
    } else if (data.decision === 'STEP_UP') {
      decisionClass = 'badge-step-up';
      icon = '🔐';
    }

    badgeDecision.classList.add(decisionClass);
    decisionText.innerText = data.decision.replace('_', ' ');
    decisionIcon.innerText = icon;

    resRiskTier.innerText = data.risk_level;
    resLatency.innerText = `${data.processing_time_ms} ms`;
    resModelVer.innerText = `v${data.model_version || '2.0.0'}`;

    // Sub-factors
    valRuleScore.innerText = `${data.rule_score.toFixed(1)}`;
    barRule.style.width = `${Math.min(100, data.rule_score)}%`;

    valMlProb.innerText = `${(data.fraud_probability * 100).toFixed(1)}%`;
    barMl.style.width = `${data.fraud_probability * 100}%`;

    valIsoScore.innerText = `${data.anomaly_score.toFixed(3)}`;
    barIso.style.width = `${data.anomaly_score * 100}%`;

    valBehScore.innerText = `${(data.behavior_score || 0).toFixed(1)}`;
    barBeh.style.width = `${Math.min(100, data.behavior_score || 0)}%`;

    // Render Reasons
    reasonsList.innerHTML = '';
    if (data.reasons && data.reasons.length > 0) {
      data.reasons.forEach(r => {
        const li = document.createElement('li');
        li.className = 'reason-item';
        if (data.risk_score >= 80) li.classList.add('danger');
        else if (data.risk_score >= 60) li.classList.add('warning');
        else li.classList.add('normal');
        li.innerText = r;
        reasonsList.appendChild(li);
      });
    } else {
      const li = document.createElement('li');
      li.className = 'reason-item normal';
      li.innerText = 'No abnormal flags triggered. Normal behavioral parameters.';
      reasonsList.appendChild(li);
    }

    // Render Feature Contributions
    contribBars.innerHTML = '';
    if (data.feature_contributions) {
      Object.entries(data.feature_contributions).forEach(([name, pct]) => {
        const row = document.createElement('div');
        row.className = 'contrib-row';
        row.innerHTML = `
          <div class="contrib-header">
            <span>${name}</span>
            <span><strong>${pct}%</strong></span>
          </div>
          <div class="contrib-bar-wrap">
            <div class="contrib-bar-fill" style="width: ${pct}%"></div>
          </div>
        `;
        contribBars.appendChild(row);
      });
    }

    // Update alert count badge in header
    if (data.decision === 'BLOCK' || data.decision === 'MANUAL_REVIEW') {
      const cur = parseInt(badgeAlertsCount.innerText || '0', 10);
      badgeAlertsCount.innerText = cur + 1;
    }
  }

  function animateGauge(targetScore) {
    // 440 is the perimeter (2 * pi * 70)
    const maxOffset = 440;
    const targetOffset = maxOffset - (targetScore / 100) * maxOffset;

    gaugeBar.style.strokeDashoffset = targetOffset;

    // Stroke color based on risk level
    if (targetScore >= 80) {
      gaugeBar.style.stroke = '#ef4444'; // Crimson
    } else if (targetScore >= 60) {
      gaugeBar.style.stroke = '#f97316'; // Orange
    } else if (targetScore >= 30) {
      gaugeBar.style.stroke = '#f59e0b'; // Amber
    } else {
      gaugeBar.style.stroke = '#10b981'; // Emerald
    }

    // Number roll animation
    let current = 0;
    const step = targetScore / 25;
    const timer = setInterval(() => {
      current += step;
      if ((step > 0 && current >= targetScore) || (step <= 0 && current <= targetScore)) {
        current = targetScore;
        clearInterval(timer);
      }
      resScoreNum.innerText = current.toFixed(1);
    }, 15);
  }

  // -------------------------------------------------------------------------
  // 4. Quick Feedback Buttons
  // -------------------------------------------------------------------------
  btnQuickFraud.addEventListener('click', async () => {
    if (!currentTxnId) {
      showToast('No active transaction evaluated yet.', 'danger');
      return;
    }
    await submitFeedback(currentTxnId, 'CONFIRMED_FRAUD');
  });

  btnQuickLegit.addEventListener('click', async () => {
    if (!currentTxnId) {
      showToast('No active transaction evaluated yet.', 'danger');
      return;
    }
    await submitFeedback(currentTxnId, 'LEGITIMATE');
  });

  async function submitFeedback(txnId, verdict) {
    try {
      const res = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: txnId,
          verdict: verdict,
          analyst_id: 'ANALYST_DASHBOARD',
        }),
      });

      if (res.ok) {
        showToast(`Saved verdict: ${verdict} for ${txnId}`, 'success');
        loadAlerts();
      }
    } catch (e) {
      showToast(`Feedback error: ${e.message}`, 'danger');
    }
  }

  // -------------------------------------------------------------------------
  // 5. Alerts and Transactions Feed
  // -------------------------------------------------------------------------
  document.getElementById('btn-refresh-alerts').addEventListener('click', () => loadAlerts(true));
  document.getElementById('btn-refresh-recent').addEventListener('click', () => loadRecentTransactions(true));

  async function loadAlerts(isUserClick = false) {
    const btn = document.getElementById('btn-refresh-alerts');
    const icon = btn ? btn.querySelector('.icon-refresh') : null;
    const lbl = document.getElementById('lbl-refresh-alerts-text');
    
    if (isUserClick && icon) icon.classList.add('spin');
    if (isUserClick && lbl) lbl.innerText = 'Refreshing...';

    try {
      const res = await fetch(`/fraud/alerts?limit=25&_t=${Date.now()}`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const alerts = await res.json();

      badgeAlertsCount.innerText = alerts.filter(a => a.status === 'OPEN').length;

      if (alerts.length === 0) {
        tbodyAlerts.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 2rem; color: var(--text-muted);">No active high-priority fraud alerts.</td></tr>`;
      } else {
        tbodyAlerts.innerHTML = alerts.map(a => `
          <tr class="${isUserClick ? 'table-row-updated' : ''}">
            <td><code>${a.alert_id}</code></td>
            <td><code>${a.transaction_id}</code></td>
            <td>${formatTime(a.created_at)}</td>
            <td><strong style="color: ${a.risk_score >= 80 ? 'var(--accent-crimson)' : 'var(--accent-amber)'};">${a.risk_score.toFixed(1)}</strong></td>
            <td><span class="tag-active ${a.risk_level === 'CRITICAL' ? 'tag-danger' : 'tag-warning'}">${a.risk_level}</span></td>
            <td><strong>${a.status}</strong></td>
            <td style="max-width: 280px; font-size: 0.75rem; color: var(--text-secondary);">${(a.reasons || []).slice(0, 2).join('; ') || 'Risk threshold exceeded'}</td>
            <td>
              <button class="btn-text" onclick="window.confirmFraud('${a.transaction_id}')" style="color: #ef4444; font-weight: 600;">🚨 Fraud</button> |
              <button class="btn-text" onclick="window.confirmLegit('${a.transaction_id}')" style="color: #10b981; font-weight: 600;">✓ Legit</button>
            </td>
          </tr>
        `).join('');
      }

      if (isUserClick) {
        showToast(`Alerts queue refreshed: ${alerts.length} alerts loaded`, 'success');
      }
    } catch (e) {
      console.warn('Could not load alerts', e);
      if (isUserClick) showToast(`Failed to refresh alerts: ${e.message}`, 'danger');
    } finally {
      if (icon) icon.classList.remove('spin');
      if (lbl) lbl.innerText = 'Refresh Alerts';
    }
  }

  async function loadRecentTransactions(isUserClick = false) {
    const btn = document.getElementById('btn-refresh-recent');
    const icon = btn ? btn.querySelector('.icon-refresh') : null;
    const lbl = document.getElementById('lbl-refresh-recent-text');

    if (isUserClick && icon) icon.classList.add('spin');
    if (isUserClick && lbl) lbl.innerText = 'Refreshing...';

    try {
      const res = await fetch(`/transactions/recent?limit=25&_t=${Date.now()}`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const txns = await res.json();

      if (txns.length === 0) {
        tbodyRecent.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 2rem; color: var(--text-muted);">No transactions evaluated yet.</td></tr>`;
      } else {
        tbodyRecent.innerHTML = txns.map(t => `
          <tr class="${isUserClick ? 'table-row-updated' : ''}">
            <td><code>${t.transaction_id}</code></td>
            <td>${formatTime(t.timestamp)}</td>
            <td>${t.customer_id}</td>
            <td><strong>₹${Number(t.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></td>
            <td>${t.transaction_type}</td>
            <td><strong>${t.risk_score.toFixed(1)}</strong></td>
            <td><span class="tag-active ${t.decision === 'BLOCK' ? 'tag-danger' : (t.decision === 'ALLOW' ? '' : 'tag-warning')}">${t.decision}</span></td>
            <td>${t.processing_time_ms.toFixed(1)} ms</td>
          </tr>
        `).join('');
      }

      if (isUserClick) {
        showToast(`Transaction feed refreshed: ${txns.length} records loaded`, 'success');
      }
    } catch (e) {
      console.warn('Could not load recent txns', e);
      if (isUserClick) showToast(`Failed to refresh feed: ${e.message}`, 'danger');
    } finally {
      if (icon) icon.classList.remove('spin');
      if (lbl) lbl.innerText = 'Refresh Feed';
    }
  }

  window.confirmFraud = (id) => submitFeedback(id, 'CONFIRMED_FRAUD');
  window.confirmLegit = (id) => submitFeedback(id, 'LEGITIMATE');

  // -------------------------------------------------------------------------
  // 6. Model Benchmarks
  // -------------------------------------------------------------------------
  async function loadBenchmarks() {
    try {
      const res = await fetch('/model/performance');
      if (!res.ok) return;
      const data = await res.json();

      if (data.benchmarks) {
        tbodyBenchmarks.innerHTML = data.benchmarks.map(b => `
          <tr>
            <td><strong>${b.model}</strong></td>
            <td>${b.pr_auc.toFixed(3)}</td>
            <td>${b.f1.toFixed(3)}</td>
            <td>${(b.pr_auc * 1.03).toFixed(3)}</td>
            <td>${b.latency_ms} ms</td>
          </tr>
        `).join('');
      }

      if (data.feature_importances) {
        featImportanceBars.innerHTML = Object.entries(data.feature_importances)
          .slice(0, 7)
          .map(([feat, weight]) => `
            <div class="contrib-row">
              <div class="contrib-header">
                <span><code>${feat}</code></span>
                <span><strong>${(weight * 100).toFixed(1)}%</strong></span>
              </div>
              <div class="contrib-bar-wrap">
                <div class="contrib-bar-fill" style="width: ${weight * 100}%;"></div>
              </div>
            </div>
          `).join('');
      }
    } catch (e) {
      console.warn('Could not load benchmarks', e);
    }
  }

  // -------------------------------------------------------------------------
  // 7. System Health Status
  // -------------------------------------------------------------------------
  async function checkSystemHealth() {
    try {
      const res = await fetch('/system/status');
      if (res.ok) {
        const data = await res.json();
        document.getElementById('lbl-api-status').innerText = 'NOMINAL';
        document.getElementById('lbl-db-status').innerText = data.components.database || 'CONNECTED';
      }
    } catch (e) {
      document.getElementById('lbl-api-status').innerText = 'OFFLINE';
    }
  }

  // Helper: Toast Notifications
  function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function formatTime(isoStr) {
    if (!isoStr) return '--:--';
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  // Initial Boot
  loadPresets();
  checkSystemHealth();
  // Auto-run initial evaluate with default form values
  evalForm.dispatchEvent(new Event('submit'));
});
