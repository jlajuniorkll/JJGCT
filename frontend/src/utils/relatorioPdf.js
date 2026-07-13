import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { format, differenceInSeconds } from 'date-fns';

const PAGE_W = 210;
const PAGE_H = 297;
const MARGIN = 15;
const CONTENT_W = PAGE_W - MARGIN * 2;

const COLORS = {
  ink: [20, 24, 31],
  inkSoft: [91, 100, 114],
  inkFaint: [136, 145, 160],
  line: [215, 219, 226],
  lineStrong: [183, 191, 203],
  accent: [29, 78, 216],
  accentSoft: [238, 242, 251],
  good: [15, 122, 77],
  white: [255, 255, 255],
};

const IMAGE_URL_RE = /\.(png|jpe?g|gif|webp)$/i;

export const formatTimeDiff = (start, end, pausas = []) => {
  const safeSecondsBetween = (a, b) => Math.max(0, differenceInSeconds(a, b));
  let diff = safeSecondsBetween(end, start);
  (pausas || []).forEach((p) => {
    if (p.inicio && p.fim) {
      diff -= safeSecondsBetween(new Date(p.fim), new Date(p.inicio));
    }
  });
  diff = Math.max(0, diff);
  const hrs = Math.floor(diff / 3600);
  const mins = Math.floor((diff % 3600) / 60);
  return `${hrs}h ${mins}m`;
};

const fmtBRL = (value) => {
  const n = Number(value) || 0;
  return `R$ ${n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const fmtHoras = (value) => String(value || '0:00:00').split('.')[0];

const resolveUrl = (baseURL, path) => {
  if (!path) return null;
  const base = String(baseURL || '').replace(/\/+$/, '');
  const normalized = String(path).replace(/^\/+/, '');
  return `${base}/${normalized}`;
};

const truncateToWidth = (doc, text, maxWidth) => {
  let s = String(text ?? '');
  if (maxWidth <= 0 || doc.getTextWidth(s) <= maxWidth) return s;
  while (s.length > 0 && doc.getTextWidth(`${s}…`) > maxWidth) {
    s = s.slice(0, -1);
  }
  return s ? `${s}…` : '';
};

const ensureSpace = (doc, y, needed) => {
  if (y + needed > PAGE_H - MARGIN) {
    doc.addPage();
    return MARGIN;
  }
  return y;
};

async function loadImageAsPngDataUrl(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error('Falha ao carregar comprovante');
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  try {
    const img = await new Promise((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = reject;
      el.src = objectUrl;
    });
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    canvas.getContext('2d').drawImage(img, 0, 0);
    return {
      dataUrl: canvas.toDataURL('image/png'),
      width: img.naturalWidth,
      height: img.naturalHeight,
    };
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

function drawHeader(doc, viagem, clientesTexto) {
  const y0 = MARGIN;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7.5);
  doc.setTextColor(...COLORS.accent);
  doc.text('VIAGEM CORPORATIVA', MARGIN, y0 + 3, { charSpace: 0.3 });

  const titleMaxWidth = CONTENT_W - 62;
  doc.setFontSize(16);
  doc.setTextColor(...COLORS.ink);
  doc.text(truncateToWidth(doc, clientesTexto || 'Viagem', titleMaxWidth), MARGIN, y0 + 11);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9.5);
  doc.setTextColor(...COLORS.inkSoft);
  doc.text(truncateToWidth(doc, viagem.motivo || '', titleMaxWidth), MARGIN, y0 + 17);

  const rightX = MARGIN + CONTENT_W;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(6.8);
  doc.setTextColor(...COLORS.inkFaint);
  doc.text('ID DA VIAGEM', rightX, y0 + 2.5, { align: 'right', charSpace: 0.25 });
  doc.setFontSize(11);
  doc.setTextColor(...COLORS.ink);
  doc.text(`#${viagem.id}`, rightX, y0 + 7.5, { align: 'right' });

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(6.8);
  doc.setTextColor(...COLORS.inkFaint);
  doc.text('EMITIDO EM', rightX, y0 + 13, { align: 'right', charSpace: 0.25 });
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(...COLORS.inkSoft);
  doc.text(format(new Date(), 'dd/MM/yyyy HH:mm'), rightX, y0 + 17.5, { align: 'right' });

  const ruleY = y0 + 21;
  doc.setDrawColor(...COLORS.ink);
  doc.setLineWidth(0.5);
  doc.line(MARGIN, ruleY, MARGIN + CONTENT_W, ruleY);

  return ruleY + 7;
}

function drawKpiStrip(doc, y, kpis) {
  const boxH = 15;
  const colW = CONTENT_W / kpis.length;
  doc.setDrawColor(...COLORS.line);
  doc.setLineWidth(0.3);
  doc.rect(MARGIN, y, CONTENT_W, boxH);
  kpis.forEach((k, i) => {
    const x = MARGIN + i * colW;
    if (i > 0) doc.line(x, y, x, y + boxH);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.4);
    doc.setTextColor(...COLORS.inkFaint);
    doc.text(k.label.toUpperCase(), x + 4, y + 5.5, { charSpace: 0.2 });
    doc.setFontSize(11.5);
    doc.setTextColor(...(k.color || COLORS.ink));
    doc.text(k.value, x + 4, y + 11.5);
  });
  return y + boxH + 8;
}

function drawSectionTitle(doc, x, y, width, title) {
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7.6);
  doc.setTextColor(...COLORS.ink);
  doc.text(title.toUpperCase(), x, y, { charSpace: 0.25 });
  const textW = doc.getTextWidth(title.toUpperCase()) + 1.5;
  doc.setDrawColor(...COLORS.line);
  doc.setLineWidth(0.3);
  doc.line(x + textW + 2, y - 1.3, x + width, y - 1.3);
  return y + 5;
}

function drawFieldRow(doc, x, y, width, label, value) {
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(...COLORS.inkFaint);
  const labelText = String(label);
  const labelWidth = doc.getTextWidth(labelText);
  doc.text(labelText, x, y);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...COLORS.ink);
  const maxValueWidth = width - labelWidth - 4;
  doc.text(truncateToWidth(doc, value ?? '--', maxValueWidth), x + width, y, { align: 'right' });
  doc.setDrawColor(...COLORS.line);
  doc.setLineWidth(0.15);
  doc.line(x, y + 1.6, x + width, y + 1.6);
  return y + 6;
}

function drawTransportStrip(doc, y, cells) {
  const boxH = 15.5;
  const colW = CONTENT_W / cells.length;
  doc.setDrawColor(...COLORS.line);
  doc.setLineWidth(0.3);
  doc.rect(MARGIN, y, CONTENT_W, boxH);
  const innerW = colW - 6;
  cells.forEach((c, i) => {
    const x = MARGIN + i * colW;
    if (i > 0) doc.line(x, y, x, y + boxH);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.2);
    doc.setTextColor(...COLORS.inkFaint);
    doc.text(truncateToWidth(doc, c.label.toUpperCase(), innerW), x + 3, y + 5, { charSpace: 0.2 });
    doc.setFontSize(8.4);
    doc.setTextColor(...COLORS.ink);
    doc.text(truncateToWidth(doc, c.value ?? '--', innerW), x + 3, y + 10);
    if (c.sub) {
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.2);
      doc.setTextColor(...COLORS.inkSoft);
      doc.text(truncateToWidth(doc, c.sub, innerW), x + 3, y + 13.5);
    }
  });
  return y + boxH + 8;
}

function drawTable(doc, y, { title, head, body, foot, columnStyles }) {
  y = ensureSpace(doc, y, 18);
  y = drawSectionTitle(doc, MARGIN, y, CONTENT_W, title);
  autoTable(doc, {
    startY: y,
    margin: { left: MARGIN, right: MARGIN, bottom: MARGIN },
    head: [head],
    body,
    foot: foot ? [foot] : undefined,
    styles: {
      font: 'helvetica',
      fontSize: 8,
      textColor: COLORS.ink,
      cellPadding: 1.8,
      lineColor: COLORS.line,
      lineWidth: 0.15,
      valign: 'middle',
      minCellHeight: 7,
    },
    headStyles: {
      fillColor: COLORS.ink,
      textColor: COLORS.white,
      fontStyle: 'bold',
      fontSize: 6.8,
    },
    footStyles: {
      fillColor: COLORS.white,
      textColor: COLORS.ink,
      fontStyle: 'bold',
      fontSize: 9,
      lineWidth: { top: 0.5 },
    },
    alternateRowStyles: { fillColor: COLORS.accentSoft },
    columnStyles,
  });
  return doc.lastAutoTable.finalY + 8;
}

function drawFooter(doc, y) {
  y = ensureSpace(doc, y, 26);
  y += 4;
  const gap = 10;
  const colW = (CONTENT_W - gap) / 2;
  doc.setDrawColor(...COLORS.lineStrong);
  doc.setLineWidth(0.3);
  doc.line(MARGIN, y, MARGIN + colW, y);
  doc.line(MARGIN + colW + gap, y, MARGIN + CONTENT_W, y);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(6.6);
  doc.setTextColor(...COLORS.inkFaint);
  doc.text('ASSINATURA DO COLABORADOR', MARGIN + colW / 2, y + 4, { align: 'center', charSpace: 0.2 });
  doc.text('ASSINATURA GESTORIA', MARGIN + colW + gap + colW / 2, y + 4, { align: 'center', charSpace: 0.2 });
  y += 12;
  doc.setFont('helvetica', 'italic');
  doc.setFontSize(6.6);
  doc.setTextColor(...COLORS.inkFaint);
  doc.text('Documento gerado eletronicamente pelo sistema Corporate Travel.', PAGE_W / 2, y, { align: 'center' });
  return y;
}

export async function gerarRelatorioPDF(report, { includeReceipts = true, apiBaseURL = '' } = {}) {
  const { viagem, distancia_percorrida_km: distancia, total_horas_trabalhadas: horas, total_despesas: totalDespesas } = report;
  const clientes = viagem?.clientes || [];
  const clientesTexto = clientes.join(', ') || 'Viagem';

  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  doc.setProperties({ title: `Relatório Viagem #${viagem.id}` });

  let y = drawHeader(doc, viagem, clientesTexto);

  y = drawKpiStrip(doc, y, [
    { label: 'Distância', value: `${distancia ?? 0} km` },
    { label: 'Horas trab.', value: fmtHoras(horas) },
    { label: 'Despesas', value: fmtBRL(totalDespesas), color: COLORS.good },
    { label: 'Status', value: String(viagem.status || '').replace('_', ' ').toUpperCase(), color: COLORS.accent },
  ]);

  // Período real + Clientes | Equipe participante
  const gap = 8;
  const colW = (CONTENT_W - gap) / 2;
  const leftX = MARGIN;
  const rightX = MARGIN + colW + gap;
  const sectionTop = y;

  let leftY = drawSectionTitle(doc, leftX, sectionTop, colW, 'Período real');
  leftY = drawFieldRow(doc, leftX, leftY, colW, 'Saída', viagem.data_hora_real_saida ? format(new Date(viagem.data_hora_real_saida), "dd MMM, HH:mm'h'") : 'Não registrada');
  leftY = drawFieldRow(doc, leftX, leftY, colW, 'Retorno', viagem.data_hora_real_chegada ? format(new Date(viagem.data_hora_real_chegada), "dd MMM, HH:mm'h'") : 'Não registrada');
  leftY = drawFieldRow(doc, leftX, leftY, colW, 'Clientes', clientes.join(', ') || '--');

  let rightY = drawSectionTitle(doc, rightX, sectionTop, colW, 'Equipe participante');
  (viagem.participantes || []).forEach((p) => {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.2);
    const roleText = String(p.tipousuario || '').toUpperCase();
    const roleWidth = doc.getTextWidth(roleText);

    doc.setFontSize(8.2);
    doc.setTextColor(...COLORS.ink);
    const maxNameWidth = colW - roleWidth - 6;
    doc.text(truncateToWidth(doc, p.nome || '', maxNameWidth), rightX, rightY);

    doc.setFontSize(6.2);
    doc.setTextColor(...COLORS.inkFaint);
    doc.text(roleText, rightX + colW, rightY, { align: 'right', charSpace: 0.2 });
    rightY += 5.5;
  });

  y = Math.max(leftY, rightY) + 3;

  // Transporte
  y = ensureSpace(doc, y, 30);
  y = drawSectionTitle(doc, MARGIN, y, CONTENT_W, 'Transporte');
  y = drawTransportStrip(doc, y, [
    { label: 'Meio', value: viagem.meio_transporte || '--' },
    { label: 'Veículo', value: viagem.transporte?.veiculo?.modelo || '--', sub: viagem.transporte?.veiculo?.placa || '' },
    { label: 'Motorista', value: viagem.transporte?.motorista?.nome || '--' },
    { label: 'KM inicial', value: viagem.transporte?.km_saida ?? '--' },
    { label: 'KM final', value: viagem.transporte?.km_chegada ?? '--' },
  ]);

  // Atividades (só se houver dados)
  const atividades = viagem.atividades || [];
  if (atividades.length > 0) {
    y = drawTable(doc, y, {
      title: 'Detalhamento de atividades',
      head: ['Atividade', 'Início', 'Fim', 'Duração'],
      body: atividades.map((a) => [
        a.descricao,
        a.inicio ? format(new Date(a.inicio), 'HH:mm') : '--',
        a.fim ? format(new Date(a.fim), 'HH:mm') : '--',
        a.inicio && a.fim ? formatTimeDiff(new Date(a.inicio), new Date(a.fim), a.pausas) : '--',
      ]),
      columnStyles: { 1: { halign: 'right' }, 2: { halign: 'right' }, 3: { halign: 'right' } },
    });
  }

  // Despesas (só se houver dados)
  const despesas = viagem.despesas || [];
  if (despesas.length > 0) {
    y = drawTable(doc, y, {
      title: 'Detalhamento de despesas',
      head: ['Descrição', 'Pagamento', 'Valor'],
      body: despesas.map((d) => [d.descricao, d.forma_pagamento, fmtBRL(d.valor)]),
      foot: ['Total consolidado', '', fmtBRL(totalDespesas)],
      columnStyles: { 2: { halign: 'right' } },
    });
  }

  // Anexos (só se habilitado e houver comprovantes)
  const comExpenseAttachments = despesas.filter((d) => d.comprovante_url);
  if (includeReceipts && comExpenseAttachments.length > 0) {
    y = ensureSpace(doc, y, 14);
    y = drawSectionTitle(doc, MARGIN, y, CONTENT_W, 'Anexos de despesas');

    for (const exp of comExpenseAttachments) {
      const url = resolveUrl(apiBaseURL, exp.comprovante_url);
      if (!url) continue;

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(...COLORS.ink);

      if (IMAGE_URL_RE.test(url)) {
        try {
          const { dataUrl, width, height } = await loadImageAsPngDataUrl(url);
          const maxW = CONTENT_W;
          const maxH = 90;
          let w = maxW;
          let h = (height / width) * w;
          if (h > maxH) {
            h = maxH;
            w = (width / height) * h;
          }
          y = ensureSpace(doc, y, h + 12);
          doc.text(`${exp.descricao} — ${exp.forma_pagamento} — ${fmtBRL(exp.valor)}`, MARGIN, y);
          y += 4;
          doc.addImage(dataUrl, 'PNG', MARGIN, y, w, h);
          y += h + 7;
        } catch {
          y = ensureSpace(doc, y, 8);
          doc.text(`${exp.descricao}: comprovante indisponível`, MARGIN, y);
          y += 6;
        }
      } else {
        y = ensureSpace(doc, y, 8);
        doc.text(`${exp.descricao}: arquivo anexo — ${url}`, MARGIN, y);
        y += 6;
      }
    }
    y += 2;
  }

  drawFooter(doc, y);

  return doc;
}
