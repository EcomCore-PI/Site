(() => {
    const status = document.getElementById('metrics-status');
    if (typeof Chart === 'undefined') {
        status.textContent = 'Não foi possível carregar os gráficos. Verifique a conexão e recarregue a página.';
        status.dataset.error = 'true';
        return;
    }
    const MAX_PONTOS = 30;
    let anterior = null;
    let timer = null;
    let requisicao = null;
    const INTERVALO = 3000;
    const movimentoReduzido = window.matchMedia('(prefers-reduced-motion: reduce)');
    const formatador = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 });
    const elementos = new Map();
    const numero = valor => typeof valor === 'number' && Number.isFinite(valor) ? valor : null;
    const formato = valor => formatador.format(valor);
    const medida = (valor, unidade) => numero(valor) === null ? '—' : `${formato(valor)} ${unidade}`;
    const texto = (id, valor) => {
        if (!elementos.has(id)) elementos.set(id, document.getElementById(id));
        const elemento = elementos.get(id);
        if (elemento.textContent === valor) return;
        elemento.textContent = valor;
        if (elemento.classList.contains('kpi-value') && !movimentoReduzido.matches && elemento.animate) {
            elemento.getAnimations().forEach(animacao => animacao.cancel());
            elemento.animate([{ opacity: 0.65 }, { opacity: 1 }], { duration: 250, easing: 'ease-out' });
        }
    };
    function serie(label, cor, preenchimento = false, tracejada = false) {
        return { label, data: [], borderColor: cor, backgroundColor: cor + '18',
            fill: preenchimento, borderWidth: 2, tension: 0.25,
            pointRadius: 0, pointHoverRadius: 4, pointHitRadius: 12,
            borderDash: tracejada ? [5, 4] : [] };
    }
    function criarGrafico(id, datasets, unidade, max) {
        return new Chart(document.getElementById(id), {
            type: 'line', data: { labels: [], datasets },
            options: {
                responsive: true, maintainAspectRatio: false,
                resizeDelay: 150,
                devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2),
                animation: movimentoReduzido.matches ? false : { duration: 350, easing: 'easeOutQuart' },
                color: '#a8b8cd', font: { family: 'Inter, sans-serif', size: 16 },
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: datasets.length > 1, position: 'bottom', labels: { font: { size: 16 }, color: '#cbd5e1', boxWidth: 18, boxHeight: 2, padding: 16 } },
                    tooltip: { titleFont: { size: 16 }, bodyFont: { size: 16 }, backgroundColor: '#0f172a', titleColor: '#f8fafc', bodyColor: '#cbd5e1', borderColor: '#40526a', borderWidth: 1, padding: 12,
                        callbacks: { label: item => `${item.dataset.label}: ${medida(item.parsed.y, unidade)}` } }
                },
                scales: {
                    x: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 15 }, color: '#a8b8cd', maxTicksLimit: 4, maxRotation: 0 }, title: { font: { size: 15 }, display: true, text: 'Horário', color: '#a8b8cd' } },
                    y: { beginAtZero: true, ...(max === undefined ? {} : { max }), border: { display: false }, grid: { color: '#ffffff0b' }, ticks: { font: { size: 15 }, color: '#a8b8cd', maxTicksLimit: 5 }, title: { font: { size: 15 }, display: true, text: unidade, color: '#a8b8cd' } }
                }
            }
        });
    }
    const cpu = criarGrafico('chartCpu', [serie('CPU', '#60a5fa', true)], '%', 100);
    const ram = criarGrafico('chartRam', [serie('RAM', '#60a5fa', true)], '%', 100);
    const disco = criarGrafico('chartDisco', [serie('Disco', '#60a5fa', true)], '%', 100);
    const rede = criarGrafico('chartRede', [serie('Download', '#60a5fa'), serie('Upload', '#5eead4', false, true)], 'MiB/s');
    function adicionarPonto(grafico, horario, valores) {
        grafico.data.labels.push(horario);
        grafico.data.datasets.forEach((dataset, i) => dataset.data.push(valores[i]));
        if (grafico.data.labels.length > MAX_PONTOS) {
            grafico.data.labels.shift();
            grafico.data.datasets.forEach(dataset => dataset.data.shift());
        }
        grafico.options.animation = movimentoReduzido.matches ? false : { duration: 350, easing: 'easeOutQuart' };
        grafico.update(grafico.data.labels.length === 1 || movimentoReduzido.matches ? 'none' : undefined);
    }
    async function atualizar() {
        clearTimeout(timer);
        if (document.hidden || requisicao) return;
        const inicio = performance.now();
        const controller = new AbortController();
        requisicao = controller;
        const limite = setTimeout(() => controller.abort(), 8000);
        try {
            const resposta = await fetch('/dados', { cache: 'no-store', signal: controller.signal });
            if (!resposta.ok) throw new Error('Resposta inválida');
            const dados = await resposta.json();
            if (document.hidden) return;
            const d = Array.isArray(dados) ? dados[dados.length - 1] : dados;
            if (!d || typeof d !== 'object') throw new Error('Sem leituras');
            const horario = d.horario_formatado || new Date().toLocaleTimeString('pt-BR');
            const agora = performance.now();
            const recebidos = numero(d.bytes_recebidos), enviados = numero(d.bytes_enviados);
            let download = null, upload = null;
            // O servidor fornece contadores acumulados em MiB (bytes / 1024²).
            if (anterior && agora > anterior.tempo) {
                const segundos = (agora - anterior.tempo) / 1000;
                if (recebidos !== null && anterior.recebidos !== null && recebidos >= anterior.recebidos) download = (recebidos - anterior.recebidos) / segundos;
                if (enviados !== null && anterior.enviados !== null && enviados >= anterior.enviados) upload = (enviados - anterior.enviados) / segundos;
            }
            anterior = { tempo: agora, recebidos, enviados };
            texto('kpi-cpu', medida(d.cpu_percent, '%'));
            texto('kpi-cpu-info', `${medida(d.cpu_count, 'núcleos')} · ${medida(d.cpu_freq, 'MHz')}`);
            texto('kpi-ram', medida(d.memoria_percent, '%'));
            texto('kpi-ram-info', `${medida(d.memoria_used, 'GiB')} usados de ${medida(d.memoria_total, 'GiB')}`);
            texto('kpi-disco', medida(d.disco_percent, '%'));
            texto('kpi-disco-info', `${medida(d.disco_free, 'GiB')} livres de ${medida(d.disco_total, 'GiB')}`);
            texto('kpi-rede', medida(download, 'MiB/s'));
            texto('kpi-rede-info', download === null ? 'Calculando velocidade entre leituras…' : `Upload: ${medida(upload, 'MiB/s')}`);
            adicionarPonto(cpu, horario, [numero(d.cpu_percent)]);
            adicionarPonto(ram, horario, [numero(d.memoria_percent)]);
            adicionarPonto(disco, horario, [numero(d.disco_percent)]);
            adicionarPonto(rede, horario, [download, upload]);
            status.textContent = `Última leitura: ${horario} · Histórico de até ${MAX_PONTOS} leituras`;
            status.dataset.error = 'false';
        } catch (erro) {
            if (document.hidden) return;
            anterior = null;
            status.textContent = 'Sem atualização: verifique se o servidor de monitoramento está rodando. Os valores exibidos são da última leitura recebida.';
            status.dataset.error = 'true';
        } finally {
            clearTimeout(limite);
            requisicao = null;
            if (!document.hidden) timer = setTimeout(atualizar, Math.max(500, INTERVALO - (performance.now() - inicio)));
        }
    }
    document.addEventListener('visibilitychange', () => {
        clearTimeout(timer);
        anterior = null;
        if (document.hidden) {
            requisicao?.abort();
            [cpu, ram, disco, rede].forEach(grafico => grafico.stop());
        } else {
            atualizar();
        }
    });
    atualizar();
})();
