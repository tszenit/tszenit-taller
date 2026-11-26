
  /* ================= TS Zenit · herramientas de Precálculo ================= */
  Z.nt = function (x) { var f = Z.rat(x, 24); return f ? Z.ft(f) : Z.fx(x, 3); };
  Z.mn = function (v) { return v < 0 ? "+ " + Z.fx(-v) : "− " + Z.fx(v); };
  Z.sg = function (v) { return v > 1e-12 ? "+" : v < -1e-12 ? "−" : "0"; };
  Z.iv = function (a, b, ca, cb) { return (ca ? "[" : "(") + (a === -Infinity ? "−∞" : Z.nt(a)) + ", " + (b === Infinity ? "∞" : Z.nt(b)) + (cb ? "]" : ")"); };
  Z.res = function (items) { return '<div class="res">' + items.map(function (it) { return "<div><span>" + it[0] + "</span><b>" + it[1] + "</b></div>"; }).join("") + "</div>"; };
  Z.poly = function (c) { // coeficientes de mayor a menor grado → texto
    var n = c.length - 1, s = "";
    c.forEach(function (a, i) {
      var p = n - i; if (Math.abs(a) < 1e-12) return;
      var sgn = a < 0 ? " − " : (s ? " + " : ""), A = Math.abs(a);
      var co = (A === 1 && p > 0) ? "" : Z.nt(A);
      s += (s ? sgn : (a < 0 ? "−" : "")) + co + (p > 1 ? "x<sup>" + p + "</sup>" : p === 1 ? "x" : "");
    });
    return s || "0";
  };
  Z.lin = function (m, b, v) { // m·v + b en texto
    v = v || "x"; var s = "";
    if (Math.abs(m) > 1e-12) s = (m === 1 ? "" : m === -1 ? "−" : Z.nt(m)) + v;
    if (Math.abs(b) > 1e-12 || !s) s += s ? (b < 0 ? " − " + Z.nt(-b) : " + " + Z.nt(b)) : Z.nt(b);
    return s;
  };
  /* recta numérica con intervalos sombreados: iv = [[a,b,ca,cb],...], pts = [[x,lleno,etiqueta]] */
  Z.numline = function (x0, x1, iv, pts, extra) {
    var W = 560, H = 86, L = 22, R = 22, y = 46, sx = function (x) { return L + (Math.max(x0, Math.min(x1, x)) - x0) / (x1 - x0) * (W - L - R); };
    var g = ['<line class="ax" x1="' + L + '" y1="' + y + '" x2="' + (W - R) + '" y2="' + y + '"/>'];
    for (var k = Math.ceil(x0); k <= x1; k++) g.push('<line class="ax" x1="' + sx(k) + '" y1="' + (y - 4) + '" x2="' + sx(k) + '" y2="' + (y + 4) + '"/><text class="tick" x="' + sx(k) + '" y="' + (y + 18) + '" text-anchor="middle">' + Z.ms(k) + "</text>");
    iv.forEach(function (I) { g.push('<line class="ln ln-ok" x1="' + sx(I[0]).toFixed(1) + '" y1="' + y + '" x2="' + sx(I[1]).toFixed(1) + '" y2="' + y + '" style="stroke-width:6;opacity:.85"/>'); });
    (extra || []).forEach(function (e) { g.push('<text class="' + (e[2] || "lbl-a") + '" x="' + sx(e[0]).toFixed(1) + '" y="' + (y - 14) + '" text-anchor="middle">' + e[1] + "</text>"); });
    pts.forEach(function (p) { g.push('<circle cx="' + sx(p[0]).toFixed(1) + '" cy="' + y + '" r="6" class="' + (p[1] ? "pt" : "hole") + '"/>' + (p[2] ? '<text class="lbl" x="' + sx(p[0]).toFixed(1) + '" y="' + (y + 34) + '" text-anchor="middle">' + p[2] + "</text>" : "")); });
    return '<svg class="chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Recta numérica">' + g.join("") + "</svg>";
  };

  /* ---------- I1 · Tabla de signos para inecuaciones ---------- */
  var INEQ = {
    q: { t: "(x − a)(x − b)", f: function (x, a, b) { return (x - a) * (x - b); }, raices: function (a, b) { return [[a, "c"], [b, "c"]]; }, fac: function (a, b) { return ["x − a", "x − b"]; } },
    r: { t: "(x − a)/(x − b)", f: function (x, a, b) { return (x - a) / (x - b); }, raices: function (a, b) { return [[a, "c"], [b, "p"]]; } },
    c: { t: "(x − a)(x − b)(x − c)", f: function (x, a, b, c) { return (x - a) * (x - b) * (x - c); }, raices: function (a, b, c) { return [[a, "c"], [b, "c"], [c, "c"]]; } },
    d: { t: "(x − a)²(x − b)", f: function (x, a, b) { return (x - a) * (x - a) * (x - b); }, raices: function (a, b) { return [[a, "c"], [b, "c"]]; } }
  };
  T.signos = function (r) {
    var sg = Z.uid("sg"), so = Z.uid("so"), ia = Z.uid("a"), ib = Z.uid("b"), ic = Z.uid("c"), k = "q", op = "ge";
    r.innerHTML = Z.head("Inecuaciones", "Tabla de signos paso a paso") + Z.seg(sg, Object.keys(INEQ).map(function (q) { return [q, INEQ[q].t]; }), k) + Z.seg(so, [["gt", "&gt; 0"], ["ge", "≥ 0"], ["lt", "&lt; 0"], ["le", "≤ 0"]], op) +
      '<div class="ranges">' + Z.rng(ia, "a", -5, 5, 1, -2) + Z.rng(ib, "b", -5, 5, 1, 3) + Z.rng(ic, "c (solo en el caso de 3 factores)", -5, 5, 1, 1) + '</div><div class="stage"></div><div class="out"></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var F = INEQ[k], a = Z.val(r, ia), b = Z.val(r, ib), c = Z.val(r, ic); Z.out(r, ia, a); Z.out(r, ib, b); Z.out(r, ic, c);
      var f = function (x) { return F.f(x, a, b, c); };
      var crit = F.raices(a, b, c), pts = {};
      crit.forEach(function (p) { var x = p[0]; if (!pts[x] || p[1] === "p") pts[x] = p[1]; });
      var xs = Object.keys(pts).map(Number).sort(function (u, v) { return u - v; });
      if (k === "r" && a === b) { out.innerHTML = '<p class="err">Con a = b la expresión vale 1 para x ≠ a: elige valores distintos.</p>'; st.innerHTML = ""; return; }
      var bordes = [-Infinity].concat(xs, [Infinity]), filas = [], iv = [], strict = op === "gt" || op === "lt", pos = op === "gt" || op === "ge";
      for (var i = 0; i < bordes.length - 1; i++) {
        var lo = bordes[i], hi = bordes[i + 1], t = lo === -Infinity ? hi - 1 : hi === Infinity ? lo + 1 : (lo + hi) / 2, v = f(t), ok = pos ? v > 0 : v < 0;
        filas.push({ cls: ok ? "on" : "", c: [Z.iv(lo, hi, false, false), Z.nt(t), Z.fx(v, 3), Z.sg(v), ok ? "sí" : "no"] });
        if (ok) iv.push([lo, hi]);
      }
      // unir intervalos y decidir extremos
      var dots = xs.map(function (x) { var incl = !strict && pts[x] === "c"; return [x, incl, Z.ms(x) + (pts[x] === "p" ? " (polo)" : "")]; });
      var sol = [], cur = null;
      iv.forEach(function (I) {
        if (cur && cur[1] === I[0] && dots.some(function (d) { return d[0] === I[0] && d[1]; })) { cur[1] = I[1]; return; }
        if (cur) sol.push(cur); cur = [I[0], I[1]];
      });
      if (cur) sol.push(cur);
      var incl = function (x) { return dots.some(function (d) { return d[0] === x && d[1]; }); };
      var txt = sol.map(function (I) { return Z.iv(I[0], I[1], incl(I[0]), incl(I[1])); });
      // puntos aislados (ceros dobles con ≥ / ≤ que no tocan un intervalo)
      dots.forEach(function (d) { if (d[1] && !sol.some(function (I) { return I[0] <= d[0] && d[0] <= I[1]; })) txt.push("{" + Z.ms(d[0]) + "}"); });
      st.innerHTML = Z.numline(-7, 7, iv.map(function (I) { return [I[0] === -Infinity ? -7.5 : I[0], I[1] === Infinity ? 7.5 : I[1]]; }), dots.map(function (d) { return [d[0], d[1], d[2]]; }));
      out.innerHTML = '<div class="eq">' + F.t.replace(/x − ([abc])/g, function (_, L) { var n = { a: a, b: b, c: c }[L]; return n === 0 ? "x" : "x " + Z.mn(n); }).replace(/\(x\)/g, "x") + " " + { gt: "&gt;", ge: "≥", lt: "&lt;", le: "≤" }[op] + " 0</div>" +
        '<p class="muted" style="font-size:.86rem">1) Puntos críticos (ceros del numerador y del denominador): <b>' + xs.map(Z.ms).join(", ") + "</b>. 2) Se prueba un valor de cada intervalo. 3) Se eligen los intervalos con el signo pedido.</p>" +
        Z.tabla(["Intervalo", "Valor de prueba", "Valor", "Signo", "¿Cumple?"], filas) +
        "<p><b>Solución:</b> " + (txt.length ? txt.join(" ∪ ") : "∅ (ningún x cumple)") + "</p>" +
        (k === "r" ? '<p class="muted" style="font-size:.86rem">El cero del denominador (x = ' + Z.ms(b) + ") <b>nunca</b> se incluye, aunque la desigualdad sea ≥ o ≤.</p>" : "") +
        (k === "d" ? '<p class="muted" style="font-size:.86rem">El factor (x − a)² no cambia de signo al pasar por x = a (raíz de multiplicidad par): el signo se repite a ambos lados.</p>' : "");
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.wireSeg(r, so, function (q) { op = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I1 · Valor absoluto como distancia ---------- */
  T.absoluto = function (r) {
    var so = Z.uid("so"), ic = Z.uid("c"), ir = Z.uid("r"), op = "lt";
    r.innerHTML = Z.head("Valor absoluto", "|x − c| como distancia a c") + Z.seg(so, [["eq", "= r"], ["lt", "&lt; r"], ["le", "≤ r"], ["gt", "&gt; r"], ["ge", "≥ r"]], op) +
      '<div class="ranges">' + Z.rng(ic, "Centro c", -4, 4, 0.5, 1) + Z.rng(ir, "Radio r", -1, 5, 0.5, 2) + '</div><div class="stage"></div><div class="out"></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var c = Z.val(r, ic), R = Z.val(r, ir); Z.out(r, ic, Z.fx(c)); Z.out(r, ir, Z.fx(R));
      var sym = { eq: "=", lt: "&lt;", le: "≤", gt: "&gt;", ge: "≥" }[op], a = c - R, b = c + R, inc = op === "le" || op === "ge", sol, iv = [], pts = [];
      if (R < 0) {
        sol = (op === "gt" || op === "ge") ? "ℝ (todo x: una distancia siempre es ≥ 0 &gt; r)" : "∅ (una distancia nunca es negativa)";
        if (op === "gt" || op === "ge") iv.push([-8, 8]);
      } else if (R === 0) {
        sol = { eq: "{" + Z.nt(c) + "}", lt: "∅", le: "{" + Z.nt(c) + "}", gt: "ℝ − {" + Z.nt(c) + "}", ge: "ℝ" }[op];
        if (op === "eq" || op === "le") pts.push([c, true]); if (op === "gt") { iv.push([-8, c], [c, 8]); pts.push([c, false]); } if (op === "ge") iv.push([-8, 8]);
      } else if (op === "eq") { sol = "x = " + Z.nt(a) + " o x = " + Z.nt(b); pts.push([a, true], [b, true]); }
      else if (op === "lt" || op === "le") { sol = Z.iv(a, b, inc, inc) + "  ⇔  " + Z.nt(a) + (inc ? " ≤ " : " &lt; ") + "x" + (inc ? " ≤ " : " &lt; ") + Z.nt(b); iv.push([a, b]); pts.push([a, inc], [b, inc]); }
      else { sol = Z.iv(-Infinity, a, false, inc) + " ∪ " + Z.iv(b, Infinity, inc, false); iv.push([-8, a], [b, 8]); pts.push([a, inc], [b, inc]); }
      st.innerHTML = Z.numline(-8, 8, iv, pts, R > 0 ? [[c, "c = " + Z.fx(c)], [(a + c) / 2, "r"], [(b + c) / 2, "r"]] : [[c, "c"]]);
      out.innerHTML = '<div class="eq">|x − ' + Z.np(c) + "| " + sym + " " + Z.fx(R) + "</div><p><b>Solución:</b> " + sol + "</p>" +
        '<p class="muted" style="font-size:.86rem">' + (op === "lt" || op === "le" ? "«Menor que r» = <b>dentro</b> del intervalo centrado en c: un solo intervalo (−r &lt; x − c &lt; r)." : op === "eq" ? "«Igual a r» = los dos puntos a distancia exacta r de c." : "«Mayor que r» = <b>fuera</b>: dos semirrectas unidas con ∪ (x − c &gt; r  o  x − c &lt; −r).") + "</p>";
    }
    Z.wireSeg(r, so, function (q) { op = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I1 · Recta por dos puntos, paralela y perpendicular ---------- */
  T.recta = function (r) {
    var ids = ["x1", "y1", "x2", "y2", "qx", "qy"].map(function (s) { return Z.uid(s); });
    r.innerHTML = Z.head("Rectas", "De dos puntos a todas las formas de la ecuación") +
      '<div class="ranges">' + Z.rng(ids[0], "x₁", -6, 6, 1, -2) + Z.rng(ids[1], "y₁", -6, 6, 1, -1) + Z.rng(ids[2], "x₂", -6, 6, 1, 3) + Z.rng(ids[3], "y₂", -6, 6, 1, 2) + Z.rng(ids[4], "Punto Q: x", -6, 6, 1, 1) + Z.rng(ids[5], "Punto Q: y", -6, 6, 1, 4) +
      '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var v = ids.map(function (i) { return Z.val(r, i); }); ids.forEach(function (i, k) { Z.out(r, i, Z.ms(v[k])); });
      var x1 = v[0], y1 = v[1], x2 = v[2], y2 = v[3], qx = v[4], qy = v[5];
      var P = new Z.Plot({ x0: -8, x1: 8, y0: -8, y1: 8, W: 380, H: 380, aria: "Rectas" }).grid(1, 1, { x: 2, y: 2 });
      var html = "";
      if (x1 === x2 && y1 === y2) { out.innerHTML = '<p class="err">Los dos puntos coinciden: por un solo punto pasan infinitas rectas.</p>'; st.innerHTML = P.svg(); return; }
      if (x1 === x2) {
        Z.vline(P, x1, "ln-a"); P.seg(qx, -8, qx, 8, "ln-l dash"); Z.hline(P, qy, "ln-ok dash");
        html = Z.res([["Pendiente", "no definida"], ["Ecuación", "x = " + Z.ms(x1)], ["Paralela por Q", "x = " + Z.ms(qx)], ["Perpendicular por Q", "y = " + Z.ms(qy)]]) + '<p class="muted" style="font-size:.86rem">Recta vertical: Δx = 0, no se puede dividir. Su perpendicular es horizontal (pendiente 0).</p>';
      } else {
        var m = (y2 - y1) / (x2 - x1), n = y1 - m * x1, mp = m === 0 ? null : -1 / m;
        P.f(function (x) { return m * x + n; }, "ln-a"); P.f(function (x) { return m * (x - qx) + qy; }, "ln-l dash");
        if (mp === null) Z.vline(P, qx, "ln-ok dash"); else P.f(function (x) { return mp * (x - qx) + qy; }, "ln-ok dash");
        // forma general con enteros: (y2−y1)x − (x2−x1)y + c = 0
        var A = y2 - y1, B = -(x2 - x1), C = -(A * x1 + B * y1), g = Z.gcd(Z.gcd(A, B), C) || 1; if (A < 0 || (A === 0 && B < 0)) g = -g; A /= g; B /= g; C /= g;
        var gen = (A ? (A === 1 ? "" : A === -1 ? "−" : Z.ms(A)) + "x" : "") + (B ? (B > 0 ? (A ? " + " : "") : (A ? " − " : "−")) + (Math.abs(B) === 1 ? "" : Math.abs(B)) + "y" : "") + (C ? (C > 0 ? " + " : " − ") + Math.abs(C) : "") + " = 0";
        html = '<div class="eq">m = (' + Z.ms(y2) + " − " + Z.np(y1) + ")/(" + Z.ms(x2) + " − " + Z.np(x1) + ") = " + Z.nt(m) + "</div>" +
          Z.res([["Punto-pendiente", (y1 ? "y " + Z.mn(y1) : "y") + " = " + Z.nt(m) + (x1 ? "(x " + Z.mn(x1) + ")" : "x")], ["Principal", "y = " + Z.lin(m, n)], ["General", gen], ["Corte eje Y", "(0, " + Z.nt(n) + ")"], ["Corte eje X", m === 0 ? (n === 0 ? "todo el eje" : "no corta") : "(" + Z.nt(-n / m) + ", 0)"], ["Distancia P₁P₂", Z.fx(Math.hypot(x2 - x1, y2 - y1), 3)], ["Punto medio", "(" + Z.nt((x1 + x2) / 2) + ", " + Z.nt((y1 + y2) / 2) + ")"]]) +
          '<p style="font-size:.9rem"><span class="lat-t">Paralela por Q</span> (misma pendiente): y = ' + Z.lin(m, qy - m * qx) + "<br><span class=\"ok-t\">Perpendicular por Q</span> (m·m′ = −1): " + (mp === null ? "x = " + Z.ms(qx) : "m′ = " + Z.nt(mp) + ", y = " + Z.lin(mp, qy - mp * qx)) + "</p>";
      }
      P.pt(x1, y1, "", "P₁").pt(x2, y2, "", "P₂").pt(qx, qy, "fs", "Q");
      st.innerHTML = P.svg(); out.innerHTML = html;
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I1 · Parábola: vértice, ceros, forma canónica ---------- */
  T.parabola = function (r) {
    var ia = Z.uid("a"), ib = Z.uid("b"), ic = Z.uid("c");
    r.innerHTML = Z.head("Parábola", "y = ax² + bx + c: completar el cuadrado en vivo") +
      '<div class="ranges">' + Z.rng(ia, "a", -3, 3, 0.5, 1) + Z.rng(ib, "b", -8, 8, 1, -4) + Z.rng(ic, "c", -8, 8, 1, 3) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var a = Z.val(r, ia), b = Z.val(r, ib), c = Z.val(r, ic); Z.out(r, ia, Z.fx(a)); Z.out(r, ib, Z.ms(b)); Z.out(r, ic, Z.ms(c));
      var P = new Z.Plot({ x0: -8, x1: 8, y0: -10, y1: 10, W: 380, H: 380, aria: "Parábola" }).grid(1, 1, { x: 2, y: 2 });
      if (a === 0) { P.f(function (x) { return b * x + c; }, "ln-a"); st.innerHTML = P.svg(); out.innerHTML = '<p class="err">Con a = 0 no hay parábola: es la recta y = ' + Z.lin(b, c) + ".</p>"; return; }
      var h = -b / (2 * a), k = c - b * b / (4 * a), D = b * b - 4 * a * c;
      P.f(function (x) { return a * x * x + b * x + c; }, "ln-a"); Z.vline(P, h, "ln-w dash");
      P.pt(h, k, "fs", "V"); P.pt(0, c, "fok", "");
      var ceros = "";
      if (D > 0) { var r1 = (-b - Math.sqrt(D)) / (2 * a), r2 = (-b + Math.sqrt(D)) / (2 * a); P.pt(r1, 0, "fok").pt(r2, 0, "fok"); ceros = "x = " + Z.nt(Math.min(r1, r2)) + " y x = " + Z.nt(Math.max(r1, r2)); }
      else if (D === 0) { P.pt(h, 0, "fok"); ceros = "una raíz doble: x = " + Z.nt(h); } else ceros = "no corta el eje X (Δ &lt; 0)";
      st.innerHTML = P.svg();
      out.innerHTML = '<div class="eq">y = ' + Z.poly([a, b, c]) + "<br>y = " + (a === 1 ? "" : a === -1 ? "−" : Z.nt(a)) + "(x " + (h > 0 ? "− " + Z.nt(h) : h < 0 ? "+ " + Z.nt(-h) : "") + ")<sup>2</sup> " + (k >= 0 ? "+ " + Z.nt(k) : "− " + Z.nt(-k)) + "</div>" +
        Z.res([["Vértice", "(" + Z.nt(h) + ", " + Z.nt(k) + ")"], ["Eje de simetría", "x = " + Z.nt(h)], ["Abre hacia", a > 0 ? "arriba ∪" : "abajo ∩"], [a > 0 ? "Mínimo" : "Máximo", Z.nt(k)], ["Discriminante Δ", Z.nt(D)], ["Corte eje Y", "(0, " + Z.ms(c) + ")"], ["Recorrido", a > 0 ? "[" + Z.nt(k) + ", ∞)" : "(−∞, " + Z.nt(k) + "]"]]) +
        "<p style=\"font-size:.9rem\"><b>Ceros:</b> " + ceros + '</p><p class="muted" style="font-size:.85rem">h = −b/(2a) = ' + Z.nt(h) + " y k = f(h) = " + Z.nt(k) + ". El signo de a decide si k es mínimo o máximo; |a| decide qué tan «cerrada» es.</p>";
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I1 · Optimización con cuadráticas (corral) ---------- */
  T.corral = function (r) {
    var iL = Z.uid("L"), ix = Z.uid("x");
    r.innerHTML = Z.head("Modelo cuadrático", "Corral junto a un río: maximiza el área") + '<p class="muted" style="font-size:.88rem">Se cercan 3 lados de un rectángulo (el río es el 4.º lado). Ancho x (los dos lados perpendiculares al río), largo L − 2x.</p>' +
      '<div class="ranges">' + Z.rng(iL, "Metros de cerca L", 20, 200, 10, 120) + Z.rng(ix, "Ancho x", 0, 100, 0.5, 20) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var L = Z.val(r, iL), x = Math.min(Z.val(r, ix), L / 2); Z.out(r, iL, L + " m"); Z.out(r, ix, Z.fx(x) + " m");
      var A = function (t) { return t * (L - 2 * t); }, xo = L / 4, Am = A(xo);
      var P = new Z.Plot({ x0: 0, x1: L / 2, y0: 0, y1: Am * 1.15, W: 380, H: 300, L: 46, aria: "Área según el ancho" }).grid(L / 20, Am / 5, { x: L / 10, y: Am / 2.5 });
      P.f(A, "ln-a"); Z.vline(P, x, "ln-l dash"); P.pt(x, A(x), "fs", "").pt(xo, Am, "fok", "máx");
      st.innerHTML = P.svg();
      out.innerHTML = '<div class="eq">A(x) = x(' + L + " − 2x) = −2x<sup>2</sup> + " + L + "x</div>" + Z.res([["Ancho x", Z.fx(x) + " m"], ["Largo", Z.fx(L - 2 * x) + " m"], ["Área", Z.fx(A(x), 1) + " m²"], ["x óptimo = −b/(2a)", Z.fx(xo) + " m"], ["Área máxima", Z.fx(Am, 1) + " m²"]]) +
        '<p class="muted" style="font-size:.86rem">Dominio del modelo: 0 &lt; x &lt; ' + Z.fx(L / 2) + " (el largo debe ser positivo). El máximo está en el vértice: x = " + L + "/4.</p>";
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Transformaciones de funciones ---------- */
  var BASES = {
    x2: { t: "x²", f: function (x) { return x * x; } }, x3: { t: "x³", f: function (x) { return x * x * x; } },
    sq: { t: "√x", f: function (x) { return x < 0 ? NaN : Math.sqrt(x); } }, ab: { t: "|x|", f: Math.abs },
    inv: { t: "1/x", f: function (x) { return Math.abs(x) < 1e-9 ? NaN : 1 / x; } }, ex: { t: "2ˣ", f: function (x) { return Math.pow(2, x); } }
  };
  T.transf = function (r) {
    var sg = Z.uid("tb"), ia = Z.uid("a"), ib = Z.uid("b"), ih = Z.uid("h"), ik = Z.uid("k"), k = "x2";
    r.innerHTML = Z.head("Transformaciones", "y = a · f(b(x − h)) + k") + Z.seg(sg, Object.keys(BASES).map(function (q) { return [q, "f(x) = " + BASES[q].t]; }), k) +
      '<div class="ranges">' + Z.rng(ia, "a (vertical)", -3, 3, 0.5, 1) + Z.rng(ib, "b (horizontal)", -3, 3, 0.5, 1) + Z.rng(ih, "h (desplaza a la derecha si h > 0)", -5, 5, 0.5, 2) + Z.rng(ik, "k (sube si k > 0)", -5, 5, 0.5, -1) +
      '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var a = Z.val(r, ia), b = Z.val(r, ib), h = Z.val(r, ih), kk = Z.val(r, ik); [[ia, a], [ib, b], [ih, h], [ik, kk]].forEach(function (p) { Z.out(r, p[0], Z.fx(p[1])); });
      var F = BASES[k].f, P = new Z.Plot({ x0: -8, x1: 8, y0: -8, y1: 8, W: 380, H: 380, aria: "Transformación" }).grid(1, 1, { x: 2, y: 2 });
      P.f(F, "ln-w dash"); if (b !== 0) P.f(function (x) { return a * F(b * (x - h)) + kk; }, "ln-a", null, null, 800);
      st.innerHTML = P.svg();
      var pasos = [];
      if (b !== 0 && Math.abs(b) !== 1) pasos.push((Math.abs(b) > 1 ? "Comprime" : "Estira") + " horizontalmente por factor 1/" + Z.fx(Math.abs(b)));
      if (b < 0) pasos.push("Refleja respecto del eje Y (b &lt; 0)");
      if (h) pasos.push("Desplaza " + Z.fx(Math.abs(h)) + " unidades a la " + (h > 0 ? "derecha" : "izquierda"));
      if (Math.abs(a) !== 1 && a !== 0) pasos.push((Math.abs(a) > 1 ? "Estira" : "Comprime") + " verticalmente por factor " + Z.fx(Math.abs(a)));
      if (a < 0) pasos.push("Refleja respecto del eje X (a &lt; 0)");
      if (kk) pasos.push("Desplaza " + Z.fx(Math.abs(kk)) + " unidades hacia " + (kk > 0 ? "arriba" : "abajo"));
      var bi = b === 1 ? "" : b === -1 ? "−" : Z.fx(b), hx = h ? "x " + Z.mn(h) : "x"; out.innerHTML = '<div class="eq">y = ' + (a === 1 ? "" : a === -1 ? "−" : Z.fx(a) + "·") + "f(" + (bi && h ? bi + "(" + hx + ")" : bi + hx) + ") " + (kk ? (kk > 0 ? "+ " + Z.fx(kk) : "− " + Z.fx(-kk)) : "") + "</div>" +
        (b === 0 ? '<p class="err">b = 0 aplasta todo a una constante: elige b ≠ 0.</p>' : '<ol class="plain">' + (pasos.length ? pasos.map(function (p) { return "<li>" + p + "</li>"; }).join("") : "<li>Sin cambios: es la función original.</li>") + "</ol>") +
        '<p class="muted" style="font-size:.85rem">Punteada: f original. Lo que va <b>dentro</b> del paréntesis actúa sobre x y «al revés» (x − 2 mueve a la derecha); lo que va <b>fuera</b> actúa sobre y y «al derecho».</p>';
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Función inversa y reflejo en y = x ---------- */
  var INVS = {
    lin: { t: "f(x) = 2x + 3", f: function (x) { return 2 * x + 3; }, g: function (x) { return (x - 3) / 2; }, gi: "f⁻¹(x) = (x − 3)/2", d: "ℝ", r: "ℝ", s: ["y = 2x + 3", "x = 2y + 3 (intercambiar)", "y = (x − 3)/2"] },
    cub: { t: "f(x) = x³ − 1", f: function (x) { return x * x * x - 1; }, g: function (x) { return Math.cbrt(x + 1); }, gi: "f⁻¹(x) = ∛(x + 1)", d: "ℝ", r: "ℝ", s: ["y = x³ − 1", "x = y³ − 1", "y = ∛(x + 1)"] },
    raiz: { t: "f(x) = √(x − 1)", f: function (x) { return x < 1 ? NaN : Math.sqrt(x - 1); }, g: function (x) { return x < 0 ? NaN : x * x + 1; }, gi: "f⁻¹(x) = x² + 1, con x ≥ 0", d: "[1, ∞)", r: "[0, ∞)", s: ["y = √(x − 1), y ≥ 0", "x = √(y − 1)", "y = x² + 1, pero solo x ≥ 0 (el recorrido de f)"] },
    rac: { t: "f(x) = (x + 1)/(x − 2)", f: function (x) { return Math.abs(x - 2) < 1e-9 ? NaN : (x + 1) / (x - 2); }, g: function (x) { return Math.abs(x - 1) < 1e-9 ? NaN : (2 * x + 1) / (x - 1); }, gi: "f⁻¹(x) = (2x + 1)/(x − 1)", d: "ℝ − {2}", r: "ℝ − {1}", s: ["x = (y + 1)/(y − 2)", "x(y − 2) = y + 1 ⇒ xy − y = 2x + 1", "y(x − 1) = 2x + 1 ⇒ y = (2x + 1)/(x − 1)"] },
    exp: { t: "f(x) = 2ˣ", f: function (x) { return Math.pow(2, x); }, g: function (x) { return x <= 0 ? NaN : Math.log(x) / Math.LN2; }, gi: "f⁻¹(x) = log₂ x", d: "ℝ", r: "(0, ∞)", s: ["y = 2ˣ", "x = 2ʸ", "y = log₂ x"] }
  };
  T.inversa = function (r) {
    var sg = Z.uid("iv"), ix = Z.uid("x"), k = "lin";
    r.innerHTML = Z.head("Inversa", "La gráfica de f⁻¹ es el reflejo de f en y = x") + Z.seg(sg, Object.keys(INVS).map(function (q) { return [q, INVS[q].t]; }), k) +
      '<div class="ranges">' + Z.rng(ix, "Punto (a, f(a)) sobre f", -3, 5, 0.25, 2.5) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var F = INVS[k], a = Z.val(r, ix), fa = F.f(a); Z.out(r, ix, "a = " + Z.fx(a));
      var P = new Z.Plot({ x0: -6, x1: 8, y0: -6, y1: 8, W: 380, H: 380, aria: "f y su inversa" }).grid(1, 1, { x: 2, y: 2 });
      P.f(function (x) { return x; }, "ln-w dash"); P.f(F.f, "ln-a", null, null, 800); P.f(F.g, "ln-l", null, null, 800);
      if (isFinite(fa)) { P.pt(a, fa, "", "(a, f(a))").pt(fa, a, "fs", "(f(a), a)"); P.seg(a, fa, fa, a, "ln-ok dash"); }
      st.innerHTML = P.svg();
      out.innerHTML = Z.res([["Dominio de f", F.d], ["Recorrido de f", F.r], ["Dominio de f⁻¹", F.r], ["Recorrido de f⁻¹", F.d]]) +
        '<div class="eq">' + F.gi + "</div><ol class=\"plain\">" + F.s.map(function (s) { return "<li>" + s + "</li>"; }).join("") + "</ol>" +
        (isFinite(fa) ? '<p style="font-size:.9rem">f(' + Z.fx(a) + ") = " + Z.fx(fa) + "  ⇒  f⁻¹(" + Z.fx(fa) + ") = " + Z.fx(a) + "</p>" : '<p class="err">a = ' + Z.fx(a) + " no está en el dominio de f.</p>") +
        '<p class="muted" style="font-size:.85rem">Celeste: f · tostado: f⁻¹ · punteada: y = x. El dominio y el recorrido se intercambian.</p>';
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Tasa de cambio promedio ---------- */
  var TCP = { c: { t: "f(x) = x² − 2x", f: function (x) { return x * x - 2 * x; } }, r: { t: "f(x) = √x", f: function (x) { return x < 0 ? NaN : Math.sqrt(x); } }, e: { t: "f(x) = 2ˣ", f: function (x) { return Math.pow(2, x); } }, i: { t: "f(x) = 4/x", f: function (x) { return x === 0 ? NaN : 4 / x; } } };
  T.tcp = function (r) {
    var sg = Z.uid("tc"), ia = Z.uid("a"), ib = Z.uid("b"), k = "c";
    r.innerHTML = Z.head("Tasa de cambio promedio", "Pendiente de la recta que une dos puntos de la gráfica") + Z.seg(sg, Object.keys(TCP).map(function (q) { return [q, TCP[q].t]; }), k) +
      '<div class="ranges">' + Z.rng(ia, "a", 0, 6, 0.5, 1) + Z.rng(ib, "b", 0, 6, 0.5, 4) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var F = TCP[k].f, a = Z.val(r, ia), b = Z.val(r, ib); Z.out(r, ia, Z.fx(a)); Z.out(r, ib, Z.fx(b));
      var P = new Z.Plot({ x0: -1, x1: 7, y0: -3, y1: 25, W: 380, H: 320, aria: "Tasa de cambio promedio" }).grid(1, 1, { x: 1, y: 5 });
      P.f(F, "ln-a", null, null, 600);
      var fa = F(a), fb = F(b), ok = isFinite(fa) && isFinite(fb) && a !== b, m = ok ? (fb - fa) / (b - a) : NaN;
      if (ok) { P.f(function (x) { return fa + m * (x - a); }, "ln-l"); P.seg(a, fa, b, fa, "ln-w dash").seg(b, fa, b, fb, "ln-w dash"); P.pt(a, fa, "", "A").pt(b, fb, "", "B"); }
      st.innerHTML = P.svg();
      out.innerHTML = ok ? '<div class="eq">TCP = [f(' + Z.fx(b) + ") − f(" + Z.fx(a) + ")]/(" + Z.fx(b) + " − " + Z.np(a) + ") = (" + Z.fx(fb) + " − " + Z.np(+fa.toFixed(4)) + ")/" + Z.fx(b - a) + " = " + Z.nt(m) + "</div>" +
        Z.res([["Δy", Z.fx(fb - fa)], ["Δx", Z.fx(b - a)], ["TCP", Z.nt(m)]]) + '<p class="muted" style="font-size:.85rem">Es la pendiente de la recta (tostada) que une A y B. Si la TCP es positiva, en promedio f crece en [a, b]; si es negativa, decrece. Una recta tiene TCP constante; una curva, no.</p>' :
        '<p class="err">Elige a ≠ b dentro del dominio de f.</p>';
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Exponencial y logaritmo de base b ---------- */
  T.explog = function (r) {
    var ib = Z.uid("b"), iN = Z.uid("N");
    r.innerHTML = Z.head("Exponencial y logaritmo", "bˣ y log_b x son inversas") +
      '<div class="ranges">' + Z.rng(ib, "Base b", 0.2, 4, 0.1, 2) + Z.rng(iN, "N para resolver bˣ = N", 0.25, 20, 0.25, 8) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var b = Z.val(r, ib), N = Z.val(r, iN); Z.out(r, ib, Z.fx(b)); Z.out(r, iN, Z.fx(N));
      var P = new Z.Plot({ x0: -5, x1: 8, y0: -5, y1: 8, W: 380, H: 380, aria: "Exponencial y logaritmo" }).grid(1, 1, { x: 2, y: 2 });
      P.f(function (x) { return x; }, "ln-w dash");
      if (Math.abs(b - 1) < 1e-9) { st.innerHTML = P.svg(); out.innerHTML = '<p class="err">b = 1 no sirve como base: 1ˣ = 1 siempre y no tiene inversa.</p>'; return; }
      P.f(function (x) { return Math.pow(b, x); }, "ln-a", null, null, 600); P.f(function (x) { return x <= 0 ? NaN : Math.log(x) / Math.log(b); }, "ln-l", null, null, 900);
      P.pt(0, 1, "", "(0, 1)").pt(1, 0, "fs", "(1, 0)", 6, 16); P.pt(1, b, "fok", "(1, b)");
      var x = Math.log(N) / Math.log(b); P.pt(x, N, "fok");
      st.innerHTML = P.svg();
      out.innerHTML = Z.res([["bˣ", b > 1 ? "creciente" : "decreciente"], ["Dominio bˣ", "ℝ"], ["Recorrido bˣ", "(0, ∞)"], ["Asíntota de bˣ", "horizontal: y = 0"], ["Dominio log_b", "(0, ∞)"], ["Asíntota de log_b", "vertical: x = 0"]]) +
        '<div class="eq">' + Z.fx(b) + "<sup>x</sup> = " + Z.fx(N) + "  ⇔  x = log<sub>" + Z.fx(b) + "</sub> " + Z.fx(N) + " = ln " + Z.fx(N) + " / ln " + Z.fx(b) + " ≈ " + Z.fx(x, 4) + "</div>" +
        '<p class="muted" style="font-size:.85rem">Celeste: y = bˣ · tostado: y = log_b x. Son simétricas respecto de y = x. Si 0 &lt; b &lt; 1 ambas son decrecientes.</p>';
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Interés compuesto ---------- */
  T.interes = function (r) {
    var sg = Z.uid("n"), iP = Z.uid("P"), ir = Z.uid("r"), it = Z.uid("t"), n = "12";
    r.innerHTML = Z.head("Interés compuesto", "A = P(1 + r/n)ⁿᵗ y A = Peʳᵗ") + Z.seg(sg, [["1", "anual"], ["2", "semestral"], ["4", "trimestral"], ["12", "mensual"], ["365", "diaria"], ["c", "continua"]], n) +
      '<div class="ranges">' + Z.rng(iP, "Capital P (miles de pesos)", 100, 5000, 100, 1000) + Z.rng(ir, "Tasa anual r (%)", 1, 20, 0.5, 6) + Z.rng(it, "Años t", 1, 40, 1, 10) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var Pc = Z.val(r, iP), rr = Z.val(r, ir) / 100, t = Z.val(r, it); Z.out(r, iP, Z.fx(Pc, 0)); Z.out(r, ir, Z.fx(rr * 100, 1) + "%"); Z.out(r, it, t);
      var A = function (s) { return n === "c" ? Pc * Math.exp(rr * s) : Pc * Math.pow(1 + rr / +n, +n * s); };
      var top = A(t) * 1.1, P = new Z.Plot({ x0: 0, x1: t, y0: 0, y1: top, W: 380, H: 300, L: 50, aria: "Crecimiento del capital" }).grid(Math.max(1, Math.round(t / 10)), top / 6, { x: Math.max(1, Math.round(t / 5)), y: top / 3 });
      P.f(A, "ln-a"); P.f(function (s) { return Pc * (1 + rr * s); }, "ln-w dash"); P.pt(t, A(t), "fok");
      st.innerHTML = P.svg();
      var dup = n === "c" ? Math.log(2) / rr : Math.log(2) / (+n * Math.log(1 + rr / +n));
      out.innerHTML = '<div class="eq">' + (n === "c" ? "A = " + Z.fx(Pc, 0) + "·e<sup>" + Z.fx(rr, 3) + "·" + t + "</sup>" : "A = " + Z.fx(Pc, 0) + "(1 + " + Z.fx(rr, 3) + "/" + n + ")<sup>" + n + "·" + t + "</sup>") + "</div>" +
        Z.res([["Monto final A", Z.fx(A(t), 2)], ["Interés ganado", Z.fx(A(t) - Pc, 2)], ["Con interés simple", Z.fx(Pc * (1 + rr * t), 2)], ["Tiempo para duplicar", Z.fx(dup, 2) + " años"], ["Tasa efectiva anual", Z.fx((A(1) / Pc - 1) * 100, 3) + "%"]]) +
        '<p class="muted" style="font-size:.85rem">Punteada: interés simple (lineal). Más capitalizaciones por año dan un poco más, con techo en la capitalización continua. Para duplicar se resuelve 2 = (1 + r/n)ⁿᵗ (o 2 = eʳᵗ si es continua) usando logaritmos.</p>';
    }
    Z.wireSeg(r, sg, function (q) { n = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I3 · Circunferencia unitaria ---------- */
  var NOT = { 0: ["0", "1", "0", "0"], 30: ["π/6", "√3/2", "1/2", "√3/3"], 45: ["π/4", "√2/2", "√2/2", "1"], 60: ["π/3", "1/2", "√3/2", "√3"], 90: ["π/2", "0", "1", "no def."] };
  T.circulo = function (r) {
    var ia = Z.uid("t");
    r.innerHTML = Z.head("Circunferencia unitaria", "cos t = x, sen t = y") + '<div class="ranges">' + Z.rng(ia, "Ángulo t (grados; salta por los notables)", 0, 360, 15, 150) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function exact(deg) {
      var q = Math.floor(deg / 90) % 4, ref = deg % 180; ref = ref > 90 ? 180 - ref : ref;
      if (deg % 90 === 0) { var t = { 0: ["1", "0", "0"], 90: ["0", "1", "no def."], 180: ["−1", "0", "0"], 270: ["0", "−1", "no def."], 360: ["1", "0", "0"] }[deg]; return { c: t[0], s: t[1], t: t[2], ref: 0 }; }
      if (!NOT[ref]) return null;
      var c = Math.cos(deg * Math.PI / 180), s = Math.sin(deg * Math.PI / 180), sgn = function (v, x) { return (v < 0 ? "−" : "") + x; };
      return { c: sgn(c, NOT[ref][1]), s: sgn(s, NOT[ref][2]), t: sgn(s * c, NOT[ref][3]), ref: ref };
    }
    function rad(deg) { if (deg === 0) return "0"; var f = Z.F(deg, 180); return (f.n === 1 ? "" : f.n) + "π" + (f.d === 1 ? "" : "/" + f.d); }
    function draw() {
      var d = Z.val(r, ia), t = d * Math.PI / 180, c = Math.cos(t), s = Math.sin(t); Z.out(r, ia, d + "° = " + rad(d));
      var P = new Z.Plot({ x0: -1.4, x1: 1.4, y0: -1.4, y1: 1.4, W: 340, H: 340, aria: "Circunferencia unitaria" }).grid(0.5, 0.5, { x: 0.5, y: 0.5 });
      P.f(function (x) { return Math.sqrt(Math.max(0, 1 - x * x)); }, "ln-w", -1, 1, 300).f(function (x) { return -Math.sqrt(Math.max(0, 1 - x * x)); }, "ln-w", -1, 1, 300);
      var arc = ""; for (var i = 0; i <= 40; i++) { var u = t * i / 40; arc += (i ? "L" : "M") + P.sx(0.22 * Math.cos(u)).toFixed(1) + " " + P.sy(0.22 * Math.sin(u)).toFixed(1); }
      P.raw('<path class="ln ln-l" d="' + arc + '"/>');
      P.seg(0, 0, c, s, "ln-a").seg(c, 0, c, s, "ln-ok").seg(0, 0, c, 0, "ln-l"); P.pt(c, s, "", "P", c < 0 ? -18 : 8);
      st.innerHTML = P.svg();
      var E = exact(d), q = d % 90 === 0 ? "sobre un eje" : ["I", "II", "III", "IV"][Math.floor(d / 90) % 4];
      out.innerHTML = Z.res([["Cuadrante", q], ["Ángulo de referencia", (E ? E.ref : (d % 180 > 90 ? 180 - d % 180 : d % 180)) + "°"], ["cos t", E ? E.c : Z.fx(c, 4)], ["sen t", E ? E.s : Z.fx(s, 4)], ["tan t", E ? E.t : Z.fx(s / c, 4)]]) +
        '<p style="font-size:.9rem">Decimal: cos t ≈ ' + Z.fx(c, 4) + ", sen t ≈ " + Z.fx(s, 4) + '</p><p class="muted" style="font-size:.85rem">Signos: en el I todo positivo; en el II solo seno; en el III solo tangente; en el IV solo coseno. El valor absoluto se saca del ángulo de referencia.</p>';
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I3 · Sinusoide ---------- */
  T.sinusoide = function (r) {
    var sg = Z.uid("sf"), iA = Z.uid("A"), iB = Z.uid("B"), iC = Z.uid("C"), iD = Z.uid("D"), k = "sen";
    r.innerHTML = Z.head("Sinusoides", "y = A·sen(B(x − C)) + D") + Z.seg(sg, [["sen", "seno"], ["cos", "coseno"]], k) +
      '<div class="ranges">' + Z.rng(iA, "A", -3, 3, 0.5, 2) + Z.rng(iB, "B", 0.5, 4, 0.5, 2) + Z.rng(iC, "C (en múltiplos de π/4)", -4, 4, 1, 1) + Z.rng(iD, "D", -2, 2, 0.5, 0) + '</div><div class="stage"></div><div class="out"></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var A = Z.val(r, iA), B = Z.val(r, iB), Cq = Z.val(r, iC), C = Cq * Math.PI / 4, D = Z.val(r, iD), f = k === "sen" ? Math.sin : Math.cos;
      Z.out(r, iA, Z.fx(A)); Z.out(r, iB, Z.fx(B)); Z.out(r, iC, Cq ? (Z.ft(Z.F(Cq, 4)) + "π").replace(/^1π/, "π").replace(/^−1π/, "−π") : "0"); Z.out(r, iD, Z.fx(D));
      var P = new Z.Plot({ x0: -2 * Math.PI, x1: 2 * Math.PI, y0: -5.5, y1: 5.5, W: 620, H: 300, aria: "Sinusoide" }).grid(Math.PI / 2, 1, false);
      for (var j = -4; j <= 4; j++) if (j) P.text(j * Math.PI / 2, -0.5, (j % 2 ? (Math.abs(j) === 1 ? (j < 0 ? "−" : "") : Z.ms(j)) + "π/2" : (Math.abs(j / 2) === 1 ? (j < 0 ? "−" : "") : Z.ms(j / 2)) + "π"), "tick", "middle");
      for (var yy = -4; yy <= 4; yy += 2) if (yy) P.text(-2 * Math.PI + 0.15, yy - 0.15, Z.ms(yy), "tick");
      P.f(f, "ln-w dash"); P.f(function (x) { return A * f(B * (x - C)) + D; }, "ln-a", null, null, 900); Z.hline(P, D, "ln-ok dash");
      P.pt(C, A * f(0) + D, "fs");
      st.innerHTML = P.svg();
      var per = 2 * Math.PI / B, pf = Z.F(Math.round(2 * 4 / B), 4);
      out.innerHTML = Z.res([["Amplitud |A|", Z.fx(Math.abs(A))], ["Período 2π/B", (Z.rat(2 / B, 12) ? Z.ft(Z.rat(2 / B, 12)) : Z.fx(2 / B)) + "π ≈ " + Z.fx(per, 3)], ["Desfase C", (Cq ? Z.ft(Z.F(Cq, 4)) + "π" : "0") + (C > 0 ? " (derecha)" : C < 0 ? " (izquierda)" : "")], ["Línea media", "y = " + Z.fx(D)], ["Máximo", Z.fx(D + Math.abs(A))], ["Mínimo", Z.fx(D - Math.abs(A))]]) +
        '<p class="muted" style="font-size:.85rem">Un ciclo completo empieza en x = C y termina en x = C + 2π/B; divídelo en 4 partes iguales para ubicar ceros, máximos y mínimos. Si A &lt; 0, la curva parte hacia abajo. Ojo: en sen(2x − π/2) el desfase es π/4, no π/2 (factoriza: 2(x − π/4)).</p>';
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I3 · Resolver triángulos ---------- */
  T.triangulo = function (r) {
    var sg = Z.uid("tm"), ids = [Z.uid("p"), Z.uid("q"), Z.uid("s")], k = "LAL";
    var CASOS = { LAL: ["Lado b", "Ángulo A (°) entre b y c", "Lado c"], LLL: ["Lado a", "Lado b", "Lado c"], ALA: ["Ángulo A (°)", "Lado c (entre A y B)", "Ángulo B (°)"], LLA: ["Lado a (opuesto a A)", "Lado b", "Ángulo A (°)"] };
    var DEF = { LAL: [5, 60, 8], LLL: [7, 5, 8], ALA: [40, 10, 75], LLA: [6, 8, 35] };
    r.innerHTML = Z.head("Triángulos", "Ley de senos y ley de cosenos") + Z.seg(sg, [["LAL", "LAL (cosenos)"], ["LLL", "LLL (cosenos)"], ["ALA", "ALA (senos)"], ["LLA", "LLA (caso ambiguo)"]], k) + '<div class="fields"></div><div class="out"></div>';
    var fl = r.querySelector(".fields"), out = r.querySelector(".out"), R = Math.PI / 180;
    function campos() { fl.innerHTML = CASOS[k].map(function (l, i) { return Z.fld(ids[i], l, DEF[k][i]); }).join(""); Z.on(r, ".fields input", draw); }
    function tri(a, b, c, A, B, C, tag) {
      var area = 0.5 * b * c * Math.sin(A * R);
      return '<div class="case">' + (tag ? "<b>" + tag + "</b>" : "") + Z.res([["a", Z.fx(a, 3)], ["b", Z.fx(b, 3)], ["c", Z.fx(c, 3)], ["A", Z.fx(A, 2) + "°"], ["B", Z.fx(B, 2) + "°"], ["C", Z.fx(C, 2) + "°"], ["Área ½bc·sen A", Z.fx(area, 3)]]) + "</div>";
    }
    function draw() {
      var v = ids.map(function (i) { return Z.val(r, i); }), h = "";
      if (v.some(function (x) { return !isFinite(x) || x <= 0; })) { out.innerHTML = '<p class="err">Ingresa valores positivos.</p>'; return; }
      if (k === "LAL") { var b = v[0], A = v[1], c = v[2]; if (A >= 180) { out.innerHTML = '<p class="err">El ángulo debe ser menor que 180°.</p>'; return; }
        var a = Math.sqrt(b * b + c * c - 2 * b * c * Math.cos(A * R)), B = Math.acos((a * a + c * c - b * b) / (2 * a * c)) / R;
        h = '<ol class="plain"><li>Cosenos: a² = b² + c² − 2bc·cos A = ' + Z.fx(a * a, 3) + " ⇒ a ≈ " + Z.fx(a, 3) + "</li><li>Otro ángulo con cosenos (evita la ambigüedad del seno): cos B = (a² + c² − b²)/(2ac) ⇒ B ≈ " + Z.fx(B, 2) + "°</li><li>C = 180° − A − B</li></ol>" + tri(a, b, c, A, B, 180 - A - B); }
      if (k === "LLL") { var a = v[0], b = v[1], c = v[2];
        if (a + b <= c || a + c <= b || b + c <= a) { out.innerHTML = '<p class="err">No existe: cada lado debe ser menor que la suma de los otros dos (desigualdad triangular).</p>'; return; }
        var A = Math.acos((b * b + c * c - a * a) / (2 * b * c)) / R, B = Math.acos((a * a + c * c - b * b) / (2 * a * c)) / R;
        h = '<ol class="plain"><li>cos A = (b² + c² − a²)/(2bc) ⇒ A ≈ ' + Z.fx(A, 2) + "°</li><li>cos B = (a² + c² − b²)/(2ac) ⇒ B ≈ " + Z.fx(B, 2) + "°</li><li>C = 180° − A − B</li></ol>" + tri(a, b, c, A, B, 180 - A - B); }
      if (k === "ALA") { var A = v[0], c = v[1], B = v[2], C = 180 - A - B; if (C <= 0) { out.innerHTML = '<p class="err">A + B debe ser menor que 180°.</p>'; return; }
        var a = c * Math.sin(A * R) / Math.sin(C * R), b = c * Math.sin(B * R) / Math.sin(C * R);
        h = '<ol class="plain"><li>C = 180° − A − B = ' + Z.fx(C, 2) + "°</li><li>Senos: a/sen A = c/sen C ⇒ a ≈ " + Z.fx(a, 3) + "</li><li>b/sen B = c/sen C ⇒ b ≈ " + Z.fx(b, 3) + "</li></ol>" + tri(a, b, c, A, B, C); }
      if (k === "LLA") { var a = v[0], b = v[1], A = v[2]; if (A >= 180) { out.innerHTML = '<p class="err">El ángulo debe ser menor que 180°.</p>'; return; }
        var sB = b * Math.sin(A * R) / a, hh = b * Math.sin(A * R);
        h = '<p style="font-size:.9rem">Altura desde C: h = b·sen A ≈ ' + Z.fx(hh, 3) + ". sen B = b·sen A / a ≈ " + Z.fx(sB, 4) + "</p>";
        if (sB > 1 + 1e-12) h += '<p class="badt"><b>Ningún triángulo:</b> sen B &gt; 1 (el lado a es muy corto, a &lt; h).</p>';
        else { var B1 = Math.asin(Math.min(1, sB)) / R, B2 = 180 - B1, sols = [];
          if (A + B1 < 180) sols.push(B1); if (Math.abs(B2 - B1) > 1e-9 && A + B2 < 180) sols.push(B2);
          h += "<p><b>" + (sols.length === 2 ? "Dos triángulos" : sols.length === 1 ? "Un triángulo" : "Ningún triángulo") + "</b> (B = " + Z.fx(B1, 2) + "° o su suplemento " + Z.fx(B2, 2) + "°; vale si A + B &lt; 180°).</p>";
          sols.forEach(function (B, i) { var C = 180 - A - B, c = a * Math.sin(C * R) / Math.sin(A * R); h += tri(a, b, c, A, B, C, sols.length === 2 ? "Solución " + (i + 1) : ""); }); } }
      out.innerHTML = h;
    }
    Z.wireSeg(r, sg, function (q) { k = q; campos(); draw(); }); campos(); draw();
  };

  /* ---------- I3 · División sintética y ceros racionales ---------- */
  T.ruffini = function (r) {
    var ic = Z.uid("co"), ik = Z.uid("c");
    r.innerHTML = Z.head("División sintética", "P(x) ÷ (x − c), teorema del resto y ceros racionales") + '<div class="fields">' + Z.fld(ic, "Coeficientes de P (mayor a menor grado, con ceros)", "2 -3 -11 6") + Z.fld(ik, "c", "3") + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function divs(n) { n = Math.abs(n); var d = []; for (var i = 1; i <= n; i++) if (n % i === 0) d.push(i); return d; }
    function draw() {
      var co = Z.lista(r.querySelector("#" + ic).value), c = Z.val(r, ik);
      if (co.length < 2 || !isFinite(c)) { out.innerHTML = '<p class="err">Escribe al menos dos coeficientes y un valor de c.</p>'; return; }
      var fila = [], q = [co[0]]; fila.push("");
      for (var i = 1; i < co.length; i++) { var m = q[i - 1] * c; fila.push(Z.fx(m)); q.push(co[i] + m); }
      var R = q.pop(), Px = function (x) { return co.reduce(function (s, a) { return s * x + a; }, 0); };
      var t = '<div class="tw"><table class="tbl"><tbody><tr><td class="hi">' + Z.fx(c) + "</td>" + co.map(function (a) { return "<td>" + Z.fx(a) + "</td>"; }).join("") + "</tr><tr><td></td>" + fila.map(function (x) { return "<td>" + x + "</td>"; }).join("") + '</tr><tr><td></td>' + q.map(function (x) { return "<td><b>" + Z.fx(x) + "</b></td>"; }).join("") + '<td class="hi"><b>' + Z.fx(R) + "</b></td></tr></tbody></table></div>";
      var cand = [], ent = co.every(function (a) { return Math.round(a) === a; });
      if (ent && co[0] !== 0) {
        var a0 = co[co.length - 1], k0 = co.length - 1; while (a0 === 0 && k0 > 0) { k0--; a0 = co[k0]; }
        var ps = divs(a0), qs = divs(co[0]), seen = {};
        ps.forEach(function (p) { qs.forEach(function (qq) { var v = p / qq; [v, -v].forEach(function (w) { if (!seen[w]) { seen[w] = 1; cand.push(w); } }); }); });
        cand.sort(function (u, v) { return u - v; });
      }
      var ceros = cand.filter(function (w) { return Math.abs(Px(w)) < 1e-9; });
      out.innerHTML = t + Z.res([["Cociente Q(x)", Z.poly(q)], ["Resto R = P(c)", Z.fx(R)], ["¿x − c es factor?", Math.abs(R) < 1e-9 ? "sí (R = 0)" : "no"]]) +
        '<p style="font-size:.9rem">P(x) = (x ' + (c >= 0 ? "− " + Z.fx(c) : "+ " + Z.fx(-c)) + ")·(" + Z.poly(q) + ") " + (R >= 0 ? "+ " : "− ") + Z.fx(Math.abs(R)) + "</p>" +
        (cand.length ? '<p style="font-size:.9rem"><b>Candidatos p/q</b> (p divide al término independiente, q al coeficiente principal): ' + cand.map(function (w) { var f = Z.rat(w, 50); return '<span class="' + (ceros.indexOf(w) >= 0 ? "ok-t" : "") + '">' + (f ? Z.ft(f) : Z.fx(w)) + "</span>"; }).join(", ") + "<br>Ceros racionales: <b>" + (ceros.length ? ceros.map(function (w) { return Z.ft(Z.rat(w, 50)); }).join(", ") : "ninguno") + "</b></p>" : "") +
        '<p class="muted" style="font-size:.85rem">Baja el primer coeficiente; multiplica por c y suma en la columna siguiente. La última casilla es el resto, que coincide con P(c).</p>';
    }
    Z.on(r, ".fields input", draw); draw();
  };

  /* ---------- I3 · Sistemas 2×2 ---------- */
  T.sistema = function (r) {
    var ids = ["a1", "b1", "c1", "a2", "b2", "c2"].map(function (s) { return Z.uid(s); }), def = [2, 1, 5, 1, -1, 1];
    r.innerHTML = Z.head("Sistemas 2×2", "a₁x + b₁y = c₁ · a₂x + b₂y = c₂") + '<div class="ranges">' + ["a₁", "b₁", "c₁", "a₂", "b₂", "c₂"].map(function (l, i) { return Z.rng(ids[i], l, -6, 6, 1, def[i]); }).join("") + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function eq(a, b, c) { return (a ? (a === 1 ? "" : a === -1 ? "−" : Z.ms(a)) + "x" : "") + (b ? (b > 0 ? (a ? " + " : "") : (a ? " − " : "−")) + (Math.abs(b) === 1 ? "" : Math.abs(b)) + "y" : "") + (!a && !b ? "0" : "") + " = " + Z.ms(c); }
    function draw() {
      var v = ids.map(function (i) { return Z.val(r, i); }); ids.forEach(function (i, k) { Z.out(r, i, Z.ms(v[k])); });
      var a1 = v[0], b1 = v[1], c1 = v[2], a2 = v[3], b2 = v[4], c2 = v[5], D = a1 * b2 - a2 * b1;
      var P = new Z.Plot({ x0: -8, x1: 8, y0: -8, y1: 8, W: 380, H: 380, aria: "Sistema" }).grid(1, 1, { x: 2, y: 2 });
      function linea(a, b, c, cls) { if (b) P.f(function (x) { return (c - a * x) / b; }, cls); else if (a) Z.vline(P, c / a, cls); }
      linea(a1, b1, c1, "ln-a"); linea(a2, b2, c2, "ln-l");
      var h = '<div class="eq">' + eq(a1, b1, c1) + "<br>" + eq(a2, b2, c2) + "</div>", tipo;
      if ((!a1 && !b1) || (!a2 && !b2)) { tipo = "Una ecuación no tiene incógnitas: revisa los coeficientes."; }
      else if (D !== 0) { var x = (c1 * b2 - c2 * b1) / D, y = (a1 * c2 - a2 * c1) / D; P.pt(x, y, "fok", "(" + Z.nt(x) + ", " + Z.nt(y) + ")"); tipo = "<b>Compatible determinado:</b> solución única x = " + Z.nt(x) + ", y = " + Z.nt(y) + ". Las rectas se cortan."; }
      else { var dep = (a1 * c2 - a2 * c1 === 0) && (c1 * b2 - c2 * b1 === 0); tipo = dep ? "<b>Compatible indeterminado:</b> infinitas soluciones (es la misma recta)." : "<b>Incompatible:</b> sin solución (rectas paralelas distintas)."; }
      st.innerHTML = P.svg();
      out.innerHTML = h + Z.res([["Determinante a₁b₂ − a₂b₁", Z.ms(D)], ["Pendiente 1", b1 ? Z.nt(-a1 / b1) : "vertical"], ["Pendiente 2", b2 ? Z.nt(-a2 / b2) : "vertical"]]) + "<p>" + tipo + '</p><p class="muted" style="font-size:.85rem">Determinante ≠ 0 ⇔ pendientes distintas ⇔ solución única. Si es 0, compara también los términos libres: proporcionales → infinitas; si no → ninguna.</p>';
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- EX · Progresiones y series ---------- */
  T.progresion = function (r) {
    var sg = Z.uid("pg"), i1 = Z.uid("a1"), id = Z.uid("d"), iN = Z.uid("n"), k = "ar";
    r.innerHTML = Z.head("Progresiones", "Términos, sumas Sₙ y serie geométrica") + Z.seg(sg, [["ar", "aritmética"], ["ge", "geométrica"]], k) +
      '<div class="ranges">' + Z.rng(i1, "Primer término a₁", -10, 20, 1, 3) + Z.rng(id, "Diferencia d / razón r", -2, 4, 0.25, 0.5) + Z.rng(iN, "n", 1, 25, 1, 10) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var a = Z.val(r, i1), d = Z.val(r, id), n = Z.val(r, iN); Z.out(r, i1, Z.ms(a)); Z.out(r, id, Z.fx(d)); Z.out(r, iN, n);
      var term = function (j) { return k === "ar" ? a + (j - 1) * d : a * Math.pow(d, j - 1); }, S = [], s = 0, T_ = [];
      for (var j = 1; j <= 25; j++) { s += term(j); S.push(s); T_.push(term(j)); }
      var lim = (k === "ge" && Math.abs(d) < 1) ? a / (1 - d) : null;
      var vals = T_.slice(0, Math.max(n, 12)).concat(S.slice(0, Math.max(n, 12))).filter(isFinite), lo = Math.min(0, Math.min.apply(null, vals)), hi = Math.max(1, Math.max.apply(null, vals));
      if (hi - lo > 2000) { hi = Math.min(hi, 2000); lo = Math.max(lo, -2000); }
      var P = new Z.Plot({ x0: 0, x1: 26, y0: lo - (hi - lo) * 0.08, y1: hi + (hi - lo) * 0.08, W: 380, H: 300, L: 48, aria: "Términos y sumas" }).grid(1, (hi - lo) / 8, { x: 5, y: (hi - lo) / 4 });
      for (j = 1; j <= 25; j++) { Z.dot(P, j, T_[j - 1], j <= n ? "" : "fmut"); Z.dot(P, j, S[j - 1], j <= n ? "fok" : "fmut"); }
      if (lim !== null) Z.hline(P, lim, "ln-ok dash");
      st.innerHTML = P.svg();
      var Sn = S[n - 1];
      out.innerHTML = '<div class="eq">' + (k === "ar" ? "aₙ = a₁ + (n − 1)d · Sₙ = n(a₁ + aₙ)/2" : "aₙ = a₁·rⁿ⁻¹ · Sₙ = a₁(1 − rⁿ)/(1 − r)") + "</div>" +
        Z.res([["a" + n, Z.fx(term(n), 4)], ["S" + n, Z.fx(Sn, 4)], ["Primeros términos", T_.slice(0, 4).map(function (x) { return Z.fx(x, 3); }).join("; ") + "…"], ["Serie infinita", k === "ar" ? (a === 0 && d === 0 ? "0" : "diverge") : lim !== null ? "converge a " + Z.fx(lim, 4) : "diverge (|r| ≥ 1)"]]) +
        '<p class="muted" style="font-size:.85rem">Celeste: términos aₙ · verde: sumas Sₙ de los primeros n términos. Una serie geométrica converge solo si |r| &lt; 1, y entonces S = a₁/(1 − r).</p>';
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- EX · Decimal periódico a fracción ---------- */
  T.periodico = function (r) {
    var ie = Z.uid("e"), ia = Z.uid("an"), ip = Z.uid("p");
    r.innerHTML = Z.head("Decimales periódicos", "De decimal a fracción con la serie geométrica") + '<div class="fields">' + Z.fld(ie, "Parte entera", "2") + Z.fld(ia, "Anteperíodo (puede ir vacío)", "1") + Z.fld(ip, "Período", "36") + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function draw() {
      var E = r.querySelector("#" + ie).value.trim() || "0", A = r.querySelector("#" + ia).value.trim(), Pd = r.querySelector("#" + ip).value.trim();
      if (!/^\d+$/.test(E) || !/^\d*$/.test(A) || !/^\d+$/.test(Pd)) { out.innerHTML = '<p class="err">Usa solo dígitos; el período no puede ir vacío.</p>'; return; }
      var k = A.length, p = Pd.length, num = parseInt(E + A + Pd, 10) - parseInt(E + A, 10), den = (Math.pow(10, p) - 1) * Math.pow(10, k), f = Z.F(num, den);
      var a1 = parseInt(Pd, 10) / (Math.pow(10, p) * Math.pow(10, k)), rr = 1 / Math.pow(10, p);
      out.innerHTML = '<div class="eq">' + E + "," + A + "<span style=\"text-decoration:overline\">" + Pd + "</span> = " + Z.ft(f) + "</div>" +
        '<ol class="plain"><li>Como serie: ' + E + "," + (A || "") + " + " + Z.fx(a1, 10) + " + " + Z.fx(a1 * rr, 12) + " + … (geométrica con r = 1/10<sup>" + p + "</sup>)</li>" +
        "<li>Suma de la parte periódica: a₁/(1 − r) = " + Z.fx(a1, 10) + "/(1 − " + Z.fx(rr, 8) + ")</li>" +
        "<li>Atajo: (número sin coma − parte que no se repite) / (" + "9".repeat(p) + (k ? "0".repeat(k) : "") + ") = (" + (E + A + Pd).replace(/^0+(?=\d)/, "") + " − " + (E + A).replace(/^0+(?=\d)/, "") + ")/" + den + " = " + num + "/" + den + "</li><li>Simplificando: <b>" + Z.ft(f) + "</b></li></ol>";
    }
    Z.on(r, ".fields input", draw); draw();
  };

  /* ---------- EX · Teorema del binomio ---------- */
  T.binomio = function (r) {
    var ia = Z.uid("a"), ib = Z.uid("b"), iN = Z.uid("n"), ik = Z.uid("k");
    r.innerHTML = Z.head("Binomio de Newton", "(ax + b)ⁿ término a término") + '<div class="ranges">' + Z.rng(ia, "a", -3, 3, 1, 2) + Z.rng(ib, "b", -4, 4, 1, -1) + Z.rng(iN, "n", 1, 8, 1, 5) + Z.rng(ik, "k (resalta el término T<sub>k+1</sub>)", 0, 8, 1, 2) + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function draw() {
      var a = Z.val(r, ia), b = Z.val(r, ib), n = Z.val(r, iN), k = Math.min(Z.val(r, ik), n); [[ia, a], [ib, b], [iN, n], [ik, k]].forEach(function (p) { Z.out(r, p[0], Z.ms(p[1])); });
      var co = [], fil = [];
      for (var j = 0; j <= n; j++) { var C = Z.C(n, j), v = C * Math.pow(a, n - j) * Math.pow(b, j); co.push(v); fil.push({ cls: j === k ? "on" : "", c: ["T" + (j + 1), "C(" + n + "," + j + ") = " + C, "(" + Z.ms(a) + "x)<sup>" + (n - j) + "</sup>·(" + Z.ms(b) + ")<sup>" + j + "</sup>", Z.ms(v) + (n - j ? "x" + (n - j > 1 ? "<sup>" + (n - j) + "</sup>" : "") : "")] }); }
      out.innerHTML = '<div class="eq">(' + Z.lin(a, b) + ")<sup>" + n + "</sup> = " + Z.poly(co) + "</div>" + Z.tabla(["Término", "Coef. binomial", "Potencias", "Resultado"], fil) +
        '<p style="font-size:.9rem">T<sub>k+1</sub> = C(n, k)·(ax)<sup>n−k</sup>·b<sup>k</sup>. Fila ' + n + " del triángulo de Pascal: " + fil.map(function (_, j) { return Z.C(n, j); }).join(" · ") + '</p><p class="muted" style="font-size:.85rem">Para «el término en x<sup>m</sup>» resuelve n − k = m; para «el término independiente», n − k = 0 (o la ecuación que anule el exponente total).</p>';
    }
    Z.on(r, "input", draw); draw();
  };
