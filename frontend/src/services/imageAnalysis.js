/**
 * Client-side image analysis using HTML5 Canvas.
 * Used as a fallback when the AI backend is offline.
 * Performs real pixel-level anomaly detection using:
 *   - Local variance (texture irregularity)
 *   - Edge density (surface discontinuities)
 *   - Brightness distribution (dark spots, stains)
 */

const CANVAS_SIZE = 128; // Downscale for fast analysis

/**
 * Analyse an image File/Blob and return defect metrics.
 * @returns {{ anomalyScore, isDefect, defectType, confidence, variance, edgeDensity }}
 */
export function analyseImage(file) {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || typeof document === "undefined") {
      resolve(makeFallback());
      return;
    }

    const img = new window.Image();
    const url = URL.createObjectURL(file);

    img.onload = () => {
      try {
        const canvas = document.createElement("canvas");
        canvas.width = CANVAS_SIZE;
        canvas.height = CANVAS_SIZE;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, CANVAS_SIZE, CANVAS_SIZE);

        const { data } = ctx.getImageData(0, 0, CANVAS_SIZE, CANVAS_SIZE);
        URL.revokeObjectURL(url);

        const metrics = computeMetrics(data, CANVAS_SIZE, CANVAS_SIZE);
        resolve(classify(metrics));
      } catch {
        URL.revokeObjectURL(url);
        resolve(makeFallback());
      }
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(makeFallback());
    };

    img.src = url;
  });
}

/** Compute pixel-level quality metrics from raw RGBA data */
function computeMetrics(data, W, H) {
  const n = W * H;
  const brightness = new Float32Array(n);
  const rChannel = new Float32Array(n);
  const gChannel = new Float32Array(n);
  const bChannel = new Float32Array(n);

  for (let i = 0; i < n; i++) {
    const r = data[i * 4] / 255;
    const g = data[i * 4 + 1] / 255;
    const b = data[i * 4 + 2] / 255;
    rChannel[i] = r;
    gChannel[i] = g;
    bChannel[i] = b;
    brightness[i] = 0.299 * r + 0.587 * g + 0.114 * b;
  }

  // --- Global variance of brightness ---
  const meanB = brightness.reduce((s, v) => s + v, 0) / n;
  const variance = brightness.reduce((s, v) => s + (v - meanB) ** 2, 0) / n;

  // --- Local patch variance (detects localized anomalies) ---
  const patchSize = 16;
  const patchVariances = [];
  for (let py = 0; py < H - patchSize; py += patchSize) {
    for (let px = 0; px < W - patchSize; px += patchSize) {
      let patchSum = 0;
      let patchSumSq = 0;
      let patchN = 0;
      for (let dy = 0; dy < patchSize; dy++) {
        for (let dx = 0; dx < patchSize; dx++) {
          const v = brightness[(py + dy) * W + (px + dx)];
          patchSum += v;
          patchSumSq += v * v;
          patchN++;
        }
      }
      const pMean = patchSum / patchN;
      patchVariances.push(patchSumSq / patchN - pMean * pMean);
    }
  }
  const maxPatchVariance = patchVariances.length
    ? Math.max(...patchVariances)
    : variance;
  const meanPatchVariance =
    patchVariances.length
      ? patchVariances.reduce((s, v) => s + v, 0) / patchVariances.length
      : variance;

  // --- Edge density via Sobel approximation ---
  let edgeSum = 0;
  for (let y = 1; y < H - 1; y++) {
    for (let x = 1; x < W - 1; x++) {
      const gx =
        -brightness[(y - 1) * W + (x - 1)] +
        brightness[(y - 1) * W + (x + 1)] +
        -2 * brightness[y * W + (x - 1)] +
        2 * brightness[y * W + (x + 1)] +
        -brightness[(y + 1) * W + (x - 1)] +
        brightness[(y + 1) * W + (x + 1)];
      const gy =
        -brightness[(y - 1) * W + (x - 1)] +
        -2 * brightness[(y - 1) * W + x] +
        -brightness[(y - 1) * W + (x + 1)] +
        brightness[(y + 1) * W + (x - 1)] +
        2 * brightness[(y + 1) * W + x] +
        brightness[(y + 1) * W + (x + 1)];
      edgeSum += Math.sqrt(gx * gx + gy * gy);
    }
  }
  const edgeDensity = edgeSum / ((W - 2) * (H - 2));

  // --- Dark spot ratio (stains, holes) ---
  const darkPixels = brightness.filter((v) => v < 0.15).length;
  const darkRatio = darkPixels / n;

  // --- Colour uniformity (scratches, tears break uniformity) ---
  const meanR = rChannel.reduce((s, v) => s + v, 0) / n;
  const meanG = gChannel.reduce((s, v) => s + v, 0) / n;
  const meanB2 = bChannel.reduce((s, v) => s + v, 0) / n;
  const colourSpread = Math.abs(meanR - meanG) + Math.abs(meanG - meanB2) + Math.abs(meanR - meanB2);

  return {
    variance,
    maxPatchVariance,
    meanPatchVariance,
    edgeDensity,
    darkRatio,
    colourSpread,
    meanBrightness: meanB,
  };
}

/**
 * Classify metrics into pass/fail with anomaly score.
 * These thresholds are tuned for typical industrial inspection images:
 *   - Fabric, metal, leather, tile, bottle surfaces
 */
function classify(m) {
  // Compute localized anomaly ratio (filters out uniform woven carpet/fabric textures)
  const patchRatio = m.maxPatchVariance / (m.meanPatchVariance + 1e-5);
  
  const varianceScore = patchRatio > 2.5 ? Math.min((patchRatio - 2.5) * 2.5, 10) : 0.0;
  const darkScore = Math.min(m.darkRatio * 40, 10);
  const spreadScore = Math.min(m.colourSpread * 20, 10);

  // Weighted anomaly score
  const anomalyScore = varianceScore * 0.60 + darkScore * 0.25 + spreadScore * 0.15;

  const isDefect = anomalyScore >= 4.2;
  const confidence = Math.min(0.70 + Math.abs(anomalyScore - 4.2) * 0.04, 0.98);

  let defectType = "none";
  if (isDefect) {
    if (m.darkRatio > 0.12) defectType = "stain / hole";
    else if (patchRatio > 3.5) defectType = "surface crack";
    else if (m.colourSpread > 0.18) defectType = "colour anomaly";
    else defectType = "surface defect";
  }

  const severityScore = isDefect ? Math.min(anomalyScore * 1.15, 10) : 0;

  return {
    anomalyScore: parseFloat(anomalyScore.toFixed(2)),
    isDefect,
    defectType,
    confidence: parseFloat(confidence.toFixed(3)),
    severity_score: parseFloat(severityScore.toFixed(2)),
    severity_level: severityScore > 7 ? "critical" : severityScore > 4 ? "high" : severityScore > 0 ? "medium" : "none",
    metrics: m,
  };
}

function makeFallback() {
  return { anomalyScore: 0, isDefect: false, defectType: "none", confidence: 0.5, severity_score: 0, severity_level: "none" };
}
