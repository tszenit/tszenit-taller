
/* TS Zenit · herramientas de matemática (núcleo) */
(function () {
  "use strict";
  var T = window.TZT = {};
  var U = 0;
  var Z = window.TZM = {};
  Z.uid = function (p) { return (p || "t") + (++U); };
  Z.num = function (v) { var x = parseFloat(String(v).replace(/\s/g, "").replace(",", ".").replace("−", "-")); return x; };
  Z.ms = function (s) { return String(s).replace(/-/g, "−"); };
  Z.fx = function (x, d) {
    if (d == null) d = 3; if (!isFinite(x)) return "—";
    if (Math.abs(x) < 1e-10) x = 0;
    return Z.ms(x.toLocaleString("es-CL", { maximumFractionDigits: d }));
  };
  Z.gcd = function (a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { var t = b; b = a % b; a = t; } return a || 1; };
  Z.F = function (n, d) { if (d === 0) return null; if (d < 0) { n = -n; d = -d; } var g = Z.gcd(n, d); return { n: n / g, d: d / g }; };
  Z.fh = function (f) {   // fracción en HTML
    if (!f) return "—";
    if (f.d === 1) return Z.ms(f.n);
    return (f.n < 0 ? "−" : "") + '<span class="fr"><span>' + Math.abs(f.n) + "</span><span>" + f.d + "</span></span>";
  };
  Z.fp = function (f) { return f && f.n < 0 ? "(" + Z.fh(f) + ")" : Z.fh(f); };
  Z.np = function (n) { return n < 0 ? "(" + Z.ms(n) + ")" : String(n); };
  Z.ft = function (f) { return f ? (f.d === 1 ? Z.ms(f.n) : Z.ms(f.n) + "/" + f.d) : "—"; };
  /* decimal → fracción de denominador chico (para mostrar resultados exactos cuando se puede) */
  Z.rat = function (x, maxD) {
    maxD = maxD || 100; if (!isFinite(x)) return null;
    for (var d = 1; d <= maxD; d++) { var n = Math.round(x * d); if (Math.abs(n / d - x) < 1e-9) return Z.F(n, d); }
    return null;
  };
  Z.nice = function (x, d) { var f = Z.rat(x, 24); return f ? Z.fh(f) : Z.fx(x, d == null ? 3 : d); };
  Z.head = function (name, title) { return '<span class="lab">Herramienta · ' + name + "</span><h4>" + title + "</h4>"; };
  Z.rng = function (id, label, min, max, step, val) {
    return '<div class="range"><label for="' + id + '"><span>' + label + '</span><output id="' + id + 'o"></output></label><input type="range" id="' + id + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + val + '"></div>';
  };
  Z.fld = function (id, label, val) { return '<div class="field"><label for="' + id + '">' + label + '</label><input id="' + id + '" inputmode="decimal" autocomplete="off" value="' + val + '"></div>'; };
  Z.seg = function (id, items, cur) {
    return '<div class="seg" id="' + id + '" role="group">' + items.map(function (it) { return '<button type="button" class="sbtn" data-k="' + it[0] + '" aria-pressed="' + (String(it[0]) === String(cur)) + '">' + it[1] + "</button>"; }).join("") + "</div>";
  };
  Z.wireSeg = function (root, id, cb) {
    var el = root.querySelector("#" + id);
    el.addEventListener("click", function (e) {
      var b = e.target.closest(".sbtn"); if (!b) return;
      Array.prototype.forEach.call(el.querySelectorAll(".sbtn"), function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      cb(b.dataset.k);
    });
  };
  Z.on = function (root, sel, fn) { Array.prototype.forEach.call(root.querySelectorAll(sel), function (el) { el.addEventListener("input", fn); el.addEventListener("change", fn); }); };
  Z.val = function (root, id) { return Z.num(root.querySelector("#" + id).value); };
  Z.out = function (root, id, txt) { var o = root.querySelector("#" + id + "o"); if (o) o.textContent = txt; };
  Z.data = function (s) { return String(s).split(/[;\s]+|,(?=\s)|,(?=\S*,)/).map(function (x) { return Z.num(x); }).filter(function (x) { return isFinite(x); }); };
  Z.lista = function (s) { return String(s).replace(/,(\d)/g, ".$1").split(/[;\s,]+/).map(Z.num).filter(function (x) { return isFinite(x); }); };
  Z.fact = function (n) { var r = 1; for (var i = 2; i <= n; i++) r *= i; return r; };
  Z.C = function (n, k) { if (k < 0 || k > n) return 0; var r = 1; for (var i = 1; i <= k; i++) r = r * (n - k + i) / i; return Math.round(r); };

  /* ---------- plano cartesiano en SVG ---------- */
  Z.Plot = function (o) {
    var W = o.W || 560, H = o.H || 360, L = o.L == null ? 34 : o.L, R = o.R == null ? 14 : o.R, Tp = o.T == null ? 14 : o.T, B = o.B == null ? 28 : o.B;
    var x0 = o.x0, x1 = o.x1, y0 = o.y0, y1 = o.y1, g = [], cid = Z.uid("clip");
    var sx = function (x) { return L + (x - x0) / (x1 - x0) * (W - L - R); };
    var sy = function (y) { return H - B - (y - y0) / (y1 - y0) * (H - Tp - B); };
    var r1 = function (v) { return Math.round(v * 10) / 10; };
    this.sx = sx; this.sy = sy; this.W = W; this.H = H; this.o = o;
    this.grid = function (dx, dy, lab) {
      var x, y, k;
      for (k = Math.ceil(x0 / dx); k * dx <= x1 + 1e-9; k++) { x = k * dx; g.push('<line class="grid" x1="' + r1(sx(x)) + '" y1="' + Tp + '" x2="' + r1(sx(x)) + '" y2="' + (H - B) + '"/>'); }
      for (k = Math.ceil(y0 / dy); k * dy <= y1 + 1e-9; k++) { y = k * dy; g.push('<line class="grid" x1="' + L + '" y1="' + r1(sy(y)) + '" x2="' + (W - R) + '" y2="' + r1(sy(y)) + '"/>'); }
      var ax = (y0 <= 0 && y1 >= 0) ? sy(0) : H - B, ay = (x0 <= 0 && x1 >= 0) ? sx(0) : L;
      g.push('<line class="ax" x1="' + L + '" y1="' + r1(ax) + '" x2="' + (W - R) + '" y2="' + r1(ax) + '"/><line class="ax" x1="' + r1(ay) + '" y1="' + Tp + '" x2="' + r1(ay) + '" y2="' + (H - B) + '"/>');
      if (lab !== false) {
        var lx = lab && lab.x || dx, ly = lab && lab.y || dy;
        for (k = Math.ceil(x0 / lx); k * lx <= x1 + 1e-9; k++) { x = k * lx; if (Math.abs(x) < 1e-9 && x0 < 0) continue; g.push('<text class="tick" x="' + r1(sx(x)) + '" y="' + r1(Math.min(H - 4, ax + 14)) + '" text-anchor="middle">' + Z.fx(x, 2) + "</text>"); }
        for (k = Math.ceil(y0 / ly); !o.noy && k * ly <= y1 + 1e-9; k++) { y = k * ly; if (Math.abs(y) < 1e-9 && y0 < 0) continue; g.push('<text class="tick" x="' + r1(Math.max(12, ay - 5)) + '" y="' + r1(sy(y) + 3.5) + '" text-anchor="end">' + Z.fx(y, 2) + "</text>"); }
      }
      return this;
    };
    this.f = function (fn, cls, a, b, n) {
      a = a == null ? x0 : Math.max(a, x0); b = b == null ? x1 : Math.min(b, x1); n = n || 420;
      var d = "", pen = false, span = (y1 - y0) * 4;
      for (var i = 0; i <= n; i++) {
        var x = a + (b - a) * i / n, y = fn(x);
        if (!isFinite(y) || y > y1 + span || y < y0 - span) { pen = false; continue; }
        d += (pen ? "L" : "M") + r1(sx(x)) + " " + r1(sy(y)); pen = true;
      }
      if (d) g.push('<path class="ln ' + (cls || "ln-a") + '" clip-path="url(#' + cid + ')" d="' + d + '"/>');
      return this;
    };
    this.area = function (fn, a, b, cls) {
      var n = 160, d = "M" + r1(sx(a)) + " " + r1(sy(0));
      for (var i = 0; i <= n; i++) { var x = a + (b - a) * i / n; d += "L" + r1(sx(x)) + " " + r1(sy(fn(x))); }
      d += "L" + r1(sx(b)) + " " + r1(sy(0)) + "Z";
      g.push('<path class="' + (cls || "area") + '" clip-path="url(#' + cid + ')" d="' + d + '"/>'); return this;
    };
    this.seg = function (xa, ya, xb, yb, cls, w) { g.push('<line class="ln ' + (cls || "ln-a") + '" clip-path="url(#' + cid + ')" x1="' + r1(sx(xa)) + '" y1="' + r1(sy(ya)) + '" x2="' + r1(sx(xb)) + '" y2="' + r1(sy(yb)) + '"' + (w ? ' style="stroke-width:' + w + '"' : "") + "/>"); return this; };
    this.arrow = function (xa, ya, xb, yb, cls) {
      var X1 = sx(xa), Y1 = sy(ya), X2 = sx(xb), Y2 = sy(yb), dx = X2 - X1, dy = Y2 - Y1, Ln = Math.sqrt(dx * dx + dy * dy); if (Ln < 2) return this;
      var ux = dx / Ln, uy = dy / Ln, hx = X2 - ux * 10, hy = Y2 - uy * 10;
      g.push('<line class="ln ' + (cls || "ln-a") + '" x1="' + r1(X1) + '" y1="' + r1(Y1) + '" x2="' + r1(hx) + '" y2="' + r1(hy) + '"/><polygon class="' + (cls === "ln-l" ? "fs" : cls === "ln-ok" ? "fok" : "fa") + '" points="' + r1(X2) + "," + r1(Y2) + " " + r1(hx - uy * 5) + "," + r1(hy + ux * 5) + " " + r1(hx + uy * 5) + "," + r1(hy - ux * 5) + '"/>');
      return this;
    };
    this.pt = function (x, y, cls, lab, dx, dy, lcls) {
      if (!isFinite(x) || !isFinite(y) || x < x0 || x > x1 || y < y0 || y > y1) return this;
      g.push('<circle class="pt ' + (cls || "") + '" cx="' + r1(sx(x)) + '" cy="' + r1(sy(y)) + '" r="5"/>');
      if (lab) g.push('<text class="' + (lcls || "lbl") + '" x="' + r1(sx(x) + (dx == null ? 8 : dx)) + '" y="' + r1(sy(y) + (dy == null ? -8 : dy)) + '">' + lab + "</text>");
      return this;
    };
    this.poly = function (pts, cls) { g.push('<polygon class="' + (cls || "fa-s") + '" clip-path="url(#' + cid + ')" points="' + pts.map(function (p) { return r1(sx(p[0])) + "," + r1(sy(p[1])); }).join(" ") + '"/>'); return this; };
    this.text = function (x, y, t, cls, anchor) { g.push('<text class="' + (cls || "lbl") + '" x="' + r1(sx(x)) + '" y="' + r1(sy(y)) + '"' + (anchor ? ' text-anchor="' + anchor + '"' : "") + ">" + t + "</text>"); return this; };
    this.raw = function (s) { g.push(s); return this; };
    this.svg = function () { return '<svg class="chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + (o.aria || "Gráfico") + '"><defs><clipPath id="' + cid + '"><rect x="' + L + '" y="' + Tp + '" width="' + (W - L - R) + '" height="' + (H - Tp - B) + '"/></clipPath></defs>' + g.join("") + "</svg>"; };
  };
})();

/* TS Zenit · herramientas de Cálculo 1 · I1 Límites */
(function () {
  "use strict";
  var T = window.TZT, Z = window.TZM;
  /* utilidades propias de cálculo */
  Z.f4 = function (x) { return Z.fx(x, 4); };
  Z.f6 = function (x) { return Z.fx(x, 6); };
  Z.btn = function (id, txt, cls) { return '<button type="button" class="cbtn' + (cls ? " " + cls : "") + '" id="' + id + '">' + txt + "</button>"; };
  Z.tabla = function (cab, filas) { return '<div class="tw"><table class="tbl"><thead><tr>' + cab.map(function (c) { return "<th>" + c + "</th>"; }).join("") + "</tr></thead><tbody>" + filas.map(function (f) { return "<tr" + (f.cls ? ' class="' + f.cls + '"' : "") + ">" + (f.c || f).map(function (c) { return "<td>" + c + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table></div>"; };
  Z.dentro = function (P, x, y) { var o = P.o; return isFinite(x) && isFinite(y) && x >= o.x0 && x <= o.x1 && y >= o.y0 && y <= o.y1; };
  Z.hole = function (P, x, y) { if (!Z.dentro(P, x, y)) return P; return P.raw('<circle class="hole" cx="' + P.sx(x).toFixed(1) + '" cy="' + P.sy(y).toFixed(1) + '" r="5"/>'); };
  Z.dot = function (P, x, y, cls) { if (!Z.dentro(P, x, y)) return P; return P.raw('<circle class="pt ' + (cls || "") + '" cx="' + P.sx(x).toFixed(1) + '" cy="' + P.sy(y).toFixed(1) + '" r="5"/>'); };
  Z.vline = function (P, x, cls) { return P.seg(x, P.o.y0, x, P.o.y1, cls || "ln-w dash", 1.4); };
  Z.hline = function (P, y, cls) { return P.seg(P.o.x0, y, P.o.x1, y, cls || "ln-w dash", 1.4); };
  Z.band = function (P, a, b, horiz, cls) {   // franja vertical (x entre a y b) u horizontal (y entre a y b), recortada al área del gráfico
    var o = P.o, X0 = horiz ? o.x0 : Math.max(o.x0, Math.min(a, b)), X1 = horiz ? o.x1 : Math.min(o.x1, Math.max(a, b)), Y0 = horiz ? Math.max(o.y0, Math.min(a, b)) : o.y0, Y1 = horiz ? Math.min(o.y1, Math.max(a, b)) : o.y1;
    if (X1 <= X0 || Y1 <= Y0) return P;
    return P.raw('<rect class="' + (cls || "bandA") + '" x="' + P.sx(X0).toFixed(1) + '" y="' + P.sy(Y1).toFixed(1) + '" width="' + (P.sx(X1) - P.sx(X0)).toFixed(1) + '" height="' + (P.sy(Y0) - P.sy(Y1)).toFixed(1) + '"/>');
  };

  