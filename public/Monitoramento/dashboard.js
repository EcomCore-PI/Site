const MAX_PONTOS = 30;      // quantos pontos aparecem nos gráficos de linha
const INTERVALO = 2000;     // ms entre cada atualização

let atualizacaoAtiva = true;
let anterior = null;        // última leitura de rede (para calcular MB/s)

Chart.defaults.color = '#8f98aa';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
Chart.defaults.font.family = "'Plus Jakarta Sans', 'Segoe UI', Arial, sans-serif";

// ---------- criação dos gráficos ----------
function criarLinha(id, datasets, max) {
    return new Chart(document.getElementById(id), {
        type: 'line',
        data: { labels: [], datasets: datasets },
        options: {
            animation: false,
            scales: { y: { beginAtZero: true, max: max } },
            elements: { point: { radius: 0 }, line: { tension: 0.3 } }
        }
    });
}

function dataset(nome, cor) {
    return { label: nome, data: [], borderColor: cor, backgroundColor: cor + '33', fill: true, borderWidth: 2 };
}

const graficoCpuRam = criarLinha('grafico-cpu-ram', [
    dataset('CPU (%)', '#005AFE'),
    dataset('RAM (%)', '#00E090')
], 100);

const graficoRede = criarLinha('grafico-rede', [
    dataset('Recebida (MB/s)', '#005AFE'),
    dataset('Enviada (MB/s)', '#00E090')
]);

const graficoDisco = new Chart(document.getElementById('grafico-disco'), {
    type: 'doughnut',
    data: {
        labels: ['Usado (GB)', 'Livre (GB)'],
        datasets: [{ data: [0, 0], backgroundColor: ['#005AFE', '#2a3045'], borderWidth: 0 }]
    },
    options: { animation: false }
});

// ---------- atualização ----------
function adicionarPonto(grafico, rotulo, valores) {
    grafico.data.labels.push(rotulo);
    valores.forEach(function (v, i) { grafico.data.datasets[i].data.push(v); });

    if (grafico.data.labels.length > MAX_PONTOS) {
        grafico.data.labels.shift();
        grafico.data.datasets.forEach(function (d) { d.data.shift(); });
    }
    grafico.update();
}

function texto(id, valor) {
    document.getElementById(id).textContent = valor;
}

async function atualizarDados() {
    if (!atualizacaoAtiva) return;

    try {
        const resposta = await fetch('/dados');
        if (!resposta.ok) throw new Error('Erro HTTP: ' + resposta.status);
        const d = await resposta.json();

        // bytes_recebidos / bytes_enviados são acumulados (MB desde o boot),
        // então a velocidade é a diferença entre duas leituras dividida pelo tempo
        const agora = Date.now();
        let recebidoMBs = 0, enviadoMBs = 0;
        if (anterior) {
            const segundos = (agora - anterior.t) / 1000;
            recebidoMBs = Math.max(0, (d.bytes_recebidos - anterior.recv) / segundos);
            enviadoMBs = Math.max(0, (d.bytes_enviados - anterior.sent) / segundos);
        }
        anterior = { t: agora, recv: d.bytes_recebidos, sent: d.bytes_enviados };

        // cards
        texto('kpi-cpu', d.cpu_percent + '%');
        texto('kpi-cpu-info', d.cpu_count + ' núcleos • ' + d.cpu_freq + ' MHz');
        texto('kpi-ram', d.memoria_percent + '%');
        texto('kpi-ram-info', d.memoria_used + ' / ' + d.memoria_total + ' GB');
        texto('kpi-disco', d.disco_percent + '%');
        texto('kpi-disco-info', d.disco_free + ' GB livres de ' + d.disco_total + ' GB');
        texto('kpi-rede', recebidoMBs.toFixed(2) + ' MB/s');
        texto('kpi-rede-info', 'Enviada: ' + enviadoMBs.toFixed(2) + ' MB/s');

        // gráficos
        adicionarPonto(graficoCpuRam, d.horario_formatado, [d.cpu_percent, d.memoria_percent]);
        adicionarPonto(graficoRede, d.horario_formatado, [recebidoMBs.toFixed(2), enviadoMBs.toFixed(2)]);

        graficoDisco.data.datasets[0].data = [d.disco_used, d.disco_free];
        graficoDisco.update();

        texto('status', 'Dados atualizados');
        texto('hora', 'Última Atualização: ' + d.horario_formatado);
    } catch (erro) {
        console.error(erro);
        texto('status', 'Erro ao obter os dados (o servidor.py está rodando?)');
    }

    setTimeout(atualizarDados, INTERVALO);
}

function alternarAtualizacao() {
    atualizacaoAtiva = !atualizacaoAtiva;
    document.getElementById('botao').textContent = atualizacaoAtiva ? 'Pausar atualização' : 'Retomar atualização';

    if (atualizacaoAtiva) {
        anterior = null;   // evita um pico de rede após a pausa
        atualizarDados();
    } else {
        texto('status', 'Atualização pausada');
    }
}

window.onload = atualizarDados;