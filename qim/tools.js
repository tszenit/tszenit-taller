  /* ================= TS Zenit · herramientas de Química para Ingeniería ================= */
  var R_ = 8.314, F_ = 96485, NA_ = 6.022e23;
  var SUP = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };
  Z.sci = function (x, d) {          // notación científica legible: 1,23 · 10⁻⁵
    if (!isFinite(x)) return "—"; if (x === 0) return "0";
    var e = Math.floor(Math.log10(Math.abs(x))); if (e >= -2 && e <= 4) return Z.fx(x, d == null ? 3 : d);
    var m = x / Math.pow(10, e); if (Math.abs(m) >= 9.995) { m /= 10; e += 1; }
    return Z.fx(m, d == null ? 2 : d) + " · 10" + String(e).split("").map(function (c) { return SUP[c]; }).join("");
  };
  Z.res = Z.res || function (items) { return '<div class="res">' + items.map(function (it) { return "<div><span>" + it[0] + "</span><b>" + it[1] + "</b></div>"; }).join("") + "</div>"; };
  Z.tabla = Z.tabla || function (cab, filas) { return '<div class="tw"><table class="tbl"><thead><tr>' + cab.map(function (c) { return "<th>" + c + "</th>"; }).join("") + "</tr></thead><tbody>" + filas.map(function (f) { return "<tr" + (f.cls ? ' class="' + f.cls + '"' : "") + ">" + (f.c || f).map(function (c) { return "<td>" + c + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table></div>"; };
  Z.fl = function (id, label, val) { return Z.fld(id, label, val); };
  Z.nota = function (t) { return '<p class="muted" style="font-size:.86rem">' + t + "</p>"; };
  function biseccion(f, a, b, n) { var fa = f(a); for (var i = 0; i < (n || 200); i++) { var m = (a + b) / 2, fm = f(m); if ((fm > 0) === (fa > 0)) { a = m; fa = fm; } else b = m; } return (a + b) / 2; }
  function sub(s) { return s.replace(/([A-Za-z)])(\d+)/g, "$1<sub>$2</sub>"); }   // fórmulas: H2O → H₂O

  /* ---------- I1 · Reactivo limitante y rendimiento ---------- */
  var RX = {
    agua: { t: "2 H2 + O2 → 2 H2O", r: [["H2", 2, 2.016], ["O2", 1, 32.00]], p: ["H2O", 2, 18.016], m: [4, 40] },
    nh3: { t: "N2 + 3 H2 → 2 NH3", r: [["N2", 1, 28.02], ["H2", 3, 2.016]], p: ["NH3", 2, 17.03], m: [28, 9] },
    ch4: { t: "CH4 + 2 O2 → CO2 + 2 H2O", r: [["CH4", 1, 16.04], ["O2", 2, 32.00]], p: ["CO2", 1, 44.01], m: [16, 48] },
    fe: { t: "Fe2O3 + 3 CO → 2 Fe + 3 CO2", r: [["Fe2O3", 1, 159.7], ["CO", 3, 28.01]], p: ["Fe", 2, 55.85], m: [160, 70] },
    al: { t: "2 Al + 3 Cl2 → 2 AlCl3", r: [["Al", 2, 26.98], ["Cl2", 3, 70.90]], p: ["AlCl3", 2, 133.3], m: [27, 71] }
  };
  T.limitante = function (r) {
    var sg = Z.uid("rx"), ia = Z.uid("ma"), ib = Z.uid("mb"), ir = Z.uid("re"), k = "agua";
    r.innerHTML = Z.head("Estequiometría", "Reactivo limitante, exceso y rendimiento") + Z.seg(sg, Object.keys(RX).map(function (q) { return [q, sub(RX[q].t)]; }), k) +
      '<div class="ranges"><div class="field"><label for="' + ia + '" id="' + ia + 'l"></label><input id="' + ia + '" inputmode="decimal" autocomplete="off"></div><div class="field"><label for="' + ib + '" id="' + ib + 'l"></label><input id="' + ib + '" inputmode="decimal" autocomplete="off"></div>' + Z.rng(ir, "Rendimiento (%)", 10, 100, 1, 85) + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function set() { var X = RX[k]; r.querySelector("#" + ia + "l").innerHTML = "Masa de " + sub(X.r[0][0]) + " (g)"; r.querySelector("#" + ib + "l").innerHTML = "Masa de " + sub(X.r[1][0]) + " (g)"; r.querySelector("#" + ia).value = X.m[0]; r.querySelector("#" + ib).value = X.m[1]; draw(); }
    function draw() {
      var X = RX[k], ma = Z.val(r, ia), mb = Z.val(r, ib), re = Z.val(r, ir); Z.out(r, ir, re + " %");
      if (!(ma > 0 && mb > 0)) { out.innerHTML = '<p class="err">Ingresa masas positivas.</p>'; return; }
      var n = [ma / X.r[0][2], mb / X.r[1][2]], q = [n[0] / X.r[0][1], n[1] / X.r[1][1]], L = q[0] <= q[1] ? 0 : 1, E = 1 - L;
      var avance = q[L], np = avance * X.p[1], mp = np * X.p[2], gastoE = avance * X.r[E][1], sobraE = n[E] - gastoE;
      out.innerHTML = '<div class="eq">' + sub(X.t) + "</div>" +
        Z.tabla(["Reactivo", "Masa (g)", "M (g/mol)", "n (mol)", "n ÷ coeficiente"], X.r.map(function (s, i) { return { cls: i === L ? "on" : "", c: [sub(s[0]), Z.fx(i ? mb : ma, 3), Z.fx(s[2], 3), Z.fx(n[i], 4), Z.fx(q[i], 4) + (i === L ? " ← menor" : "")] }; })) +
        Z.res([["Limitante", sub(X.r[L][0])], ["En exceso", sub(X.r[E][0])], ["Sobra de " + sub(X.r[E][0]), Z.fx(sobraE, 4) + " mol = " + Z.fx(sobraE * X.r[E][2], 3) + " g"], ["Teórico de " + sub(X.p[0]), Z.fx(np, 4) + " mol = " + Z.fx(mp, 3) + " g"], ["Real (" + re + " %)", Z.fx(mp * re / 100, 3) + " g"]]) +
        Z.nota("El limitante es el de menor <b>n ÷ coeficiente</b>, no el de menor masa ni el de menos moles. Todo el producto se calcula desde el limitante.");
    }
    Z.wireSeg(r, sg, function (q) { k = q; set(); }); Z.on(r, "input", draw); set();
  };

  /* ---------- I1 · Disoluciones: molaridad y dilución ---------- */
  T.disolucion = function (r) {
    var im = Z.uid("m"), iM = Z.uid("M"), iV = Z.uid("V"), ia = Z.uid("a"), iV2 = Z.uid("V2");
    r.innerHTML = Z.head("Disoluciones", "Preparar y diluir una disolución") +
      '<div class="ranges">' + Z.fl(im, "Masa de soluto (g)", "5,85") + Z.fl(iM, "Masa molar del soluto (g/mol)", "58,44") + Z.fl(iV, "Volumen de disolución (mL)", "250") + Z.fl(ia, "Alícuota que se toma (mL)", "25") + Z.fl(iV2, "Volumen final tras diluir (mL)", "100") + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function draw() {
      var m = Z.val(r, im), M = Z.val(r, iM), V = Z.val(r, iV), a = Z.val(r, ia), V2 = Z.val(r, iV2);
      if (!(m > 0 && M > 0 && V > 0 && a > 0 && V2 > 0)) { out.innerHTML = '<p class="err">Ingresa valores positivos.</p>'; return; }
      if (a > V) { out.innerHTML = '<p class="err">La alícuota no puede ser mayor que la disolución preparada.</p>'; return; }
      if (V2 < a) { out.innerHTML = '<p class="err">Al diluir, el volumen final debe ser mayor o igual que la alícuota.</p>'; return; }
      var n = m / M, C1 = n / (V / 1000), na = C1 * a / 1000, C2 = na / (V2 / 1000);
      out.innerHTML = Z.res([["Moles de soluto", Z.fx(n, 4) + " mol"], ["Molaridad inicial", Z.fx(C1, 4) + " M"], ["Moles en la alícuota", Z.fx(na, 5) + " mol"], ["Molaridad final", Z.fx(C2, 4) + " M"], ["Factor de dilución", Z.fx(V2 / a, 3)]]) +
        '<div class="eq">C₁V₁ = C₂V₂ : ' + Z.fx(C1, 4) + " · " + Z.fx(a, 2) + " = " + Z.fx(C2, 4) + " · " + Z.fx(V2, 2) + "</div>" +
        Z.nota("Al diluir solo se agrega disolvente: los <b>moles de soluto no cambian</b>. Por eso C·V se conserva (los volúmenes pueden ir en mL a ambos lados).");
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I1 · Presión de vapor (Clausius-Clapeyron) ---------- */
  T.clausius = function (r) {
    var iH = Z.uid("H"), iT1 = Z.uid("T1"), iP1 = Z.uid("P1"), iT2 = Z.uid("T2"), iPx = Z.uid("Px");
    r.innerHTML = Z.head("Líquidos", "Presión de vapor y punto de ebullición (Clausius-Clapeyron)") +
      '<div class="ranges">' + Z.fl(iH, "ΔH<sub>vap</sub> (kJ/mol)", "40,7") + Z.fl(iT1, "T₁ (°C)", "100") + Z.fl(iP1, "P₁ (mmHg)", "760") + Z.rng(iT2, "T₂ (°C)", 0, 150, 1, 70) + Z.fl(iPx, "Presión externa para hallar T<sub>eb</sub> (mmHg)", "526") + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var H = Z.val(r, iH) * 1000, T1 = Z.val(r, iT1) + 273.15, P1 = Z.val(r, iP1), t2 = Z.val(r, iT2), T2 = t2 + 273.15, Px = Z.val(r, iPx); Z.out(r, iT2, t2 + " °C");
      if (!(H > 0 && T1 > 0 && P1 > 0 && Px > 0)) { out.innerHTML = '<p class="err">Ingresa valores positivos.</p>'; st.innerHTML = ""; return; }
      var P = function (T) { return P1 * Math.exp(-H / R_ * (1 / T - 1 / T1)); }, P2 = P(T2), Teb = 1 / (1 / T1 - R_ * Math.log(Px / P1) / H);
      var ymax = Math.max(P1, Px, P2) * 1.3, pl = new Z.Plot({ x0: 0, x1: 150, y0: 0, y1: ymax, W: 380, H: 300, L: 48, aria: "Presión de vapor" }).grid(25, ymax / 5, { x: 25, y: Math.round(ymax / 5) });
      pl.f(function (t) { return P(t + 273.15); }, "ln-a"); pl.seg(0, Px, 150, Px, "ln-w dash", 1.2).pt(t2, P2, "fok", Z.fx(P2, 0)).pt(Teb - 273.15, Px, "", "T_eb");
      st.innerHTML = pl.svg();
      out.innerHTML = '<div class="eq">ln(P₂/P₁) = −(ΔH<sub>vap</sub>/R)(1/T₂ − 1/T₁)</div>' +
        Z.res([["P de vapor a " + t2 + " °C", Z.fx(P2, 1) + " mmHg"], ["T de ebullición a " + Z.fx(Px, 0) + " mmHg", Z.fx(Teb - 273.15, 1) + " °C"]]) +
        Z.nota("Un líquido hierve cuando su presión de vapor iguala la presión externa: en altura (menor presión) hierve a menor temperatura. Las temperaturas van <b>siempre en kelvin</b> y ΔH en J/mol.");
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I1 · Celdas unitarias cúbicas ---------- */
  var CEL = {
    sc: { t: "Cúbica simple", Z: 1, nc: 6, a: function (r) { return 2 * r; }, rel: "a = 2r", f: Math.PI / 6 },
    bcc: { t: "Centrada en el cuerpo (BCC)", Z: 2, nc: 8, a: function (r) { return 4 * r / Math.sqrt(3); }, rel: "a√3 = 4r", f: Math.PI * Math.sqrt(3) / 8 },
    fcc: { t: "Centrada en las caras (FCC)", Z: 4, nc: 12, a: function (r) { return 2 * Math.sqrt(2) * r; }, rel: "a√2 = 4r", f: Math.PI / (3 * Math.sqrt(2)) }
  };
  function dibCelda(k) {
    var s = 150, o = 30, d = 45, P = function (x, y, z) { return [o + x * s + z * d * 0.7, o + d * 0.7 + (1 - y) * s - z * d * 0.7]; }, g = [];
    var V = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], E = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
    E.forEach(function (e) { var a = P.apply(null, V[e[0]]), b = P.apply(null, V[e[1]]); g.push('<line class="ax" x1="' + a[0] + '" y1="' + a[1] + '" x2="' + b[0] + '" y2="' + b[1] + '"/>'); });
    var at = V.slice();
    if (k === "bcc") at.push([0.5, 0.5, 0.5]);
    if (k === "fcc") at = at.concat([[0.5, 0.5, 0], [0.5, 0.5, 1], [0.5, 0, 0.5], [0.5, 1, 0.5], [0, 0.5, 0.5], [1, 0.5, 0.5]]);
    at.sort(function (A, B) { return B[2] - A[2]; }).forEach(function (p, i) { var c = P.apply(null, p), cen = (k === "bcc" && p[0] === 0.5) || (k === "fcc" && (p[0] === 0.5 || p[1] === 0.5 || p[2] === 0.5)); g.push('<circle cx="' + c[0].toFixed(1) + '" cy="' + c[1].toFixed(1) + '" r="' + (cen ? 11 : 9) + '" class="' + (cen ? "pt fok" : "pt") + '"/>'); });
    return '<svg class="chart" viewBox="0 0 230 230" role="img" aria-label="Celda unitaria">' + g.join("") + "</svg>";
  }
  T.celda = function (r) {
    var sg = Z.uid("c"), ir = Z.uid("r"), iM = Z.uid("M"), k = "fcc";
    r.innerHTML = Z.head("Estado sólido", "Celdas cúbicas: átomos, arista, empaquetamiento y densidad") + Z.seg(sg, Object.keys(CEL).map(function (q) { return [q, CEL[q].t]; }), k) +
      '<div class="ranges">' + Z.fl(ir, "Radio atómico r (pm)", "128") + Z.fl(iM, "Masa molar (g/mol)", "63,55") + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var C = CEL[k], rr = Z.val(r, ir), M = Z.val(r, iM);
      st.innerHTML = dibCelda(k);
      if (!(rr > 0 && M > 0)) { out.innerHTML = '<p class="err">Ingresa valores positivos.</p>'; return; }
      var a = C.a(rr), acm = a * 1e-10, rho = C.Z * M / (NA_ * Math.pow(acm, 3));
      out.innerHTML = Z.res([["Átomos por celda (Z)", C.Z], ["Número de coordinación", C.nc], ["Relación a–r", C.rel], ["Arista a", Z.fx(a, 1) + " pm"], ["Fracción de empaquetamiento", Z.fx(C.f * 100, 1) + " %"], ["Densidad", Z.fx(rho, 2) + " g/cm³"]]) +
        '<div class="eq">ρ = Z·M / (N<sub>A</sub>·a³), con a en cm (1 pm = 10<sup>−10</sup> cm)</div>' +
        Z.nota("Vértice cuenta 1/8, arista 1/4, cara 1/2, centro 1. Los átomos se tocan a lo largo de la arista (simple), de la diagonal del cubo (BCC) o de la diagonal de la cara (FCC). Prueba con Cu (FCC, 128 pm): da ≈ 8,9 g/cm³.");
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I1 · Difracción de rayos X (Bragg y Miller) ---------- */
  T.bragg = function (r) {
    var sg = Z.uid("c"), ia = Z.uid("a"), il = Z.uid("l"), k = "fcc";
    r.innerHTML = Z.head("Estado sólido", "Índices de Miller y ley de Bragg") + Z.seg(sg, [["sc", "Cúbica simple"], ["bcc", "BCC"], ["fcc", "FCC"]], k) +
      '<div class="ranges">' + Z.fl(ia, "Arista a (pm)", "361,5") + Z.fl(il, "Longitud de onda λ (pm)", "154,1") + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function permitido(h, kk, l) { if (k === "sc") return true; if (k === "bcc") return (h + kk + l) % 2 === 0; var p = [h % 2, kk % 2, l % 2]; return p[0] === p[1] && p[1] === p[2]; }
    function draw() {
      var a = Z.val(r, ia), lam = Z.val(r, il);
      if (!(a > 0 && lam > 0)) { out.innerHTML = '<p class="err">Ingresa valores positivos.</p>'; return; }
      var planos = [[1, 0, 0], [1, 1, 0], [1, 1, 1], [2, 0, 0], [2, 1, 0], [2, 1, 1], [2, 2, 0], [2, 2, 1], [3, 1, 0], [3, 1, 1], [2, 2, 2]], filas = [];
      planos.forEach(function (p) {
        var s = p[0] * p[0] + p[1] * p[1] + p[2] * p[2], d = a / Math.sqrt(s), sn = lam / (2 * d), ok = permitido(p[0], p[1], p[2]);
        filas.push({ cls: ok ? "on" : "", c: ["(" + p.join("") + ")", s, Z.fx(d, 1), sn <= 1 ? Z.fx(Math.asin(sn) * 180 / Math.PI, 2) + "°" : "no difracta (sen θ > 1)", sn <= 1 ? Z.fx(2 * Math.asin(sn) * 180 / Math.PI, 2) + "°" : "—", ok ? "se observa" : "extinguida"] });
      });
      out.innerHTML = '<div class="eq">nλ = 2d sen θ  ·  d<sub>hkl</sub> = a / √(h² + k² + l²)</div>' + Z.tabla(["Plano", "h²+k²+l²", "d (pm)", "θ (n = 1)", "2θ", "En esta red"], filas) +
        Z.nota("BCC: solo planos con h + k + l par. FCC: solo con h, k, l todos pares o todos impares. Así, el primer pico de una FCC es (111) y el de una BCC es (110). Ejemplo cargado: cobre (FCC, a = 361,5 pm) con radiación Cu Kα.");
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I1 · Calorimetría: temperatura final de una mezcla ---------- */
  T.calorimetria = function (r) {
    var ids = ["m1", "c1", "t1", "m2", "c2", "t2"].map(function (x) { return Z.uid(x); });
    r.innerHTML = Z.head("Termodinámica", "Calorimetría: dos cuerpos que alcanzan el equilibrio térmico") +
      '<div class="ranges">' + Z.fl(ids[0], "Masa 1 (g) · metal", "50") + Z.fl(ids[1], "c₁ (J/g·°C)", "0,385") + Z.fl(ids[2], "T₁ (°C)", "95") + Z.fl(ids[3], "Masa 2 (g) · agua", "100") + Z.fl(ids[4], "c₂ (J/g·°C)", "4,184") + Z.fl(ids[5], "T₂ (°C)", "20") + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function draw() {
      var v = ids.map(function (i) { return Z.val(r, i); }), m1 = v[0], c1 = v[1], t1 = v[2], m2 = v[3], c2 = v[4], t2 = v[5];
      if (!(m1 > 0 && c1 > 0 && m2 > 0 && c2 > 0)) { out.innerHTML = '<p class="err">Masas y calores específicos deben ser positivos.</p>'; return; }
      var C1 = m1 * c1, C2 = m2 * c2, tf = (C1 * t1 + C2 * t2) / (C1 + C2), q1 = C1 * (tf - t1), q2 = C2 * (tf - t2);
      out.innerHTML = '<div class="eq">q₁ + q₂ = 0 ⇒ m₁c₁(T<sub>f</sub> − T₁) + m₂c₂(T<sub>f</sub> − T₂) = 0</div>' +
        Z.res([["Temperatura final", Z.fx(tf, 2) + " °C"], ["q del cuerpo 1", Z.fx(q1, 1) + " J"], ["q del cuerpo 2", Z.fx(q2, 1) + " J"], ["Capacidades calóricas", Z.fx(C1, 2) + " y " + Z.fx(C2, 2) + " J/°C"]]) +
        Z.nota("El calor que cede uno (q &lt; 0) lo gana el otro (q &gt; 0). La temperatura final queda más cerca de la del cuerpo con <b>mayor capacidad calórica</b> m·c: por eso el agua «manda».");
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I1 · Energía libre y espontaneidad ---------- */
  T.gibbs = function (r) {
    var iH = Z.uid("H"), iS = Z.uid("S"), iT = Z.uid("T");
    r.innerHTML = Z.head("Termodinámica", "ΔG = ΔH − TΔS: ¿a qué temperatura es espontánea?") +
      '<div class="ranges">' + Z.rng(iH, "ΔH (kJ/mol)", -300, 300, 1, 178) + Z.rng(iS, "ΔS (J/mol·K)", -400, 400, 1, 161) + Z.rng(iT, "T (K)", 100, 2000, 10, 298) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var H = Z.val(r, iH), S = Z.val(r, iS), Tk = Z.val(r, iT); Z.out(r, iH, H + " kJ/mol"); Z.out(r, iS, S + " J/mol·K"); Z.out(r, iT, Tk + " K");
      var G = function (t) { return H - t * S / 1000; }, g = G(Tk), Tc = S !== 0 ? H * 1000 / S : NaN;
      var lim = Math.max(Math.abs(G(0)), Math.abs(G(2000)), 50) * 1.1, pl = new Z.Plot({ x0: 0, x1: 2000, y0: -lim, y1: lim, W: 380, H: 300, L: 44, aria: "ΔG según T" }).grid(250, lim / 4, { x: 500, y: Math.round(lim / 2) });
      pl.f(G, "ln-a").pt(Tk, g, g < 0 ? "fok" : "fs", Z.fx(g, 1) + " kJ"); if (Tc > 0 && Tc < 2000) pl.pt(Tc, 0, "", Z.fx(Tc, 0) + " K", 6, 16);
      st.innerHTML = pl.svg();
      var caso = H < 0 && S > 0 ? "espontánea a toda T" : H > 0 && S < 0 ? "no espontánea a ninguna T" : H < 0 && S < 0 ? "espontánea a T bajas (T &lt; ΔH/ΔS)" : H > 0 && S > 0 ? "espontánea a T altas (T &gt; ΔH/ΔS)" : "caso límite";
      out.innerHTML = Z.res([["ΔG a " + Tk + " K", Z.fx(g, 1) + " kJ/mol"], ["¿Espontánea a esa T?", g < 0 ? "sí (ΔG &lt; 0)" : g > 0 ? "no (ΔG &gt; 0)" : "equilibrio"], ["Temperatura de cambio", Tc > 0 ? Z.fx(Tc, 1) + " K" : "no existe (mismo signo siempre)"], ["Clasificación", caso]]) +
        Z.nota("Cuidado con las unidades: ΔS viene en J/mol·K y ΔH en kJ/mol; divide ΔS por 1000 antes de restar. Cargado: CaCO₃ → CaO + CO₂ (ΔH ≈ +178 kJ, ΔS ≈ +161 J/K), espontánea sobre ≈ 1106 K.");
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Leyes de velocidad integradas ---------- */
  T.cinetica = function (r) {
    var sg = Z.uid("o"), ik = Z.uid("k"), iA = Z.uid("A"), it = Z.uid("t"), k = "1";
    var O = {
      "0": { t: "Orden 0", f: function (A0, kk, t) { return Math.max(0, A0 - kk * t); }, h: function (A0, kk) { return A0 / (2 * kk); }, lin: "[A] vs t", law: "[A] = [A]₀ − kt", u: "M/s" },
      "1": { t: "Orden 1", f: function (A0, kk, t) { return A0 * Math.exp(-kk * t); }, h: function (A0, kk) { return Math.LN2 / kk; }, lin: "ln[A] vs t", law: "ln[A] = ln[A]₀ − kt", u: "s⁻¹" },
      "2": { t: "Orden 2", f: function (A0, kk, t) { return 1 / (1 / A0 + kk * t); }, h: function (A0, kk) { return 1 / (kk * A0); }, lin: "1/[A] vs t", law: "1/[A] = 1/[A]₀ + kt", u: "M⁻¹s⁻¹" }
    };
    r.innerHTML = Z.head("Cinética", "Concentración en el tiempo según el orden") + Z.seg(sg, [["0", "Orden 0"], ["1", "Orden 1"], ["2", "Orden 2"]], k) +
      '<div class="ranges">' + Z.rng(ik, "k", 0.005, 0.2, 0.005, 0.05) + Z.rng(iA, "[A]₀ (M)", 0.1, 2, 0.05, 1) + Z.rng(it, "t (s)", 0, 100, 1, 20) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var o = O[k], kk = Z.val(r, ik), A0 = Z.val(r, iA), t = Z.val(r, it); Z.out(r, ik, Z.fx(kk, 3) + " " + o.u); Z.out(r, iA, Z.fx(A0, 2)); Z.out(r, it, t + " s");
      var At = o.f(A0, kk, t), th = o.h(A0, kk);
      var pl = new Z.Plot({ x0: 0, x1: 100, y0: 0, y1: 2.1, W: 380, H: 300, aria: "Concentración vs tiempo" }).grid(10, 0.25, { x: 20, y: 0.5 });
      pl.f(function (x) { return o.f(A0, kk, x); }, "ln-a"); pl.pt(t, At, "fok", Z.fx(At, 3) + " M"); if (th <= 100) pl.seg(th, 0, th, A0 / 2, "ln-w dash", 1.2).pt(th, A0 / 2, "", "t½");
      st.innerHTML = pl.svg();
      out.innerHTML = '<div class="eq">' + o.law + "</div>" + Z.res([["[A] a los " + t + " s", Z.fx(At, 4) + " M"], ["Vida media t½", Z.fx(th, 2) + " s"], ["Gráfico lineal", o.lin], ["Unidades de k", o.u]]) +
        Z.nota(k === "1" ? "Orden 1: la vida media <b>no depende</b> de [A]₀ (cada t½ la concentración se reduce a la mitad)." : k === "0" ? "Orden 0: la velocidad es constante y la vida media es proporcional a [A]₀; la concentración llega a 0 en un tiempo finito." : "Orden 2: la vida media es inversamente proporcional a [A]₀; cada vida media dura el doble que la anterior.");
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Ecuación de Arrhenius ---------- */
  T.arrhenius = function (r) {
    var iE = Z.uid("Ea"), ik = Z.uid("k1"), i1 = Z.uid("T1"), i2 = Z.uid("T2");
    r.innerHTML = Z.head("Cinética", "Arrhenius: cuánto acelera una reacción al calentar") +
      '<div class="ranges">' + Z.rng(iE, "Eₐ (kJ/mol)", 10, 200, 1, 50) + Z.fl(ik, "k₁ (s⁻¹) a T₁", "0,010") + Z.rng(i1, "T₁ (K)", 250, 500, 1, 298) + Z.rng(i2, "T₂ (K)", 250, 500, 1, 308) + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function draw() {
      var Ea = Z.val(r, iE) * 1000, k1 = Z.val(r, ik), T1 = Z.val(r, i1), T2 = Z.val(r, i2); Z.out(r, iE, Z.val(r, iE) + " kJ/mol"); Z.out(r, i1, T1 + " K"); Z.out(r, i2, T2 + " K");
      if (!(k1 > 0)) { out.innerHTML = '<p class="err">k₁ debe ser positiva.</p>'; return; }
      var ratio = Math.exp(-Ea / R_ * (1 / T2 - 1 / T1)), k2 = k1 * ratio, A = k1 / Math.exp(-Ea / (R_ * T1));
      out.innerHTML = '<div class="eq">ln(k₂/k₁) = −(Eₐ/R)(1/T₂ − 1/T₁)</div>' +
        Z.res([["k₂ a " + T2 + " K", Z.sci(k2, 3) + " s⁻¹"], ["k₂ / k₁", Z.fx(ratio, 3)], ["Factor de frecuencia A", Z.sci(A, 3) + " s⁻¹"], ["Pendiente de ln k vs 1/T", "−Eₐ/R = " + Z.fx(-Ea / R_, 0) + " K"]]) +
        Z.nota("Con Eₐ ≈ 50 kJ/mol, subir 10 K cerca de 25 °C casi <b>duplica</b> k. Mientras mayor Eₐ, más sensible es k a la temperatura. Un catalizador baja Eₐ (no cambia ΔH ni K).");
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Tabla ICE: resolver un equilibrio ---------- */
  var EQS = {
    hi: { t: "H2 + I2 ⇌ 2 HI", sp: ["H2", "I2", "HI"], nu: [-1, -1, 2], c0: [1, 1, 0], K: 50.5 },
    no2: { t: "N2O4 ⇌ 2 NO2", sp: ["N2O4", "NO2"], nu: [-1, 2], c0: [0.1, 0], K: 4.6e-3 },
    pcl5: { t: "PCl5 ⇌ PCl3 + Cl2", sp: ["PCl5", "PCl3", "Cl2"], nu: [-1, 1, 1], c0: [0.5, 0, 0], K: 0.042 },
    co: { t: "CO + H2O ⇌ CO2 + H2", sp: ["CO", "H2O", "CO2", "H2"], nu: [-1, -1, 1, 1], c0: [0.2, 0.2, 0.1, 0.1], K: 5.1 },
    nh3: { t: "N2 + 3 H2 ⇌ 2 NH3", sp: ["N2", "H2", "NH3"], nu: [-1, -3, 2], c0: [0.5, 1.5, 0], K: 0.5 }
  };
  T.equilibrio = function (r) {
    var sg = Z.uid("e"), iK = Z.uid("K"), box = Z.uid("c"), k = "hi";
    r.innerHTML = Z.head("Equilibrio", "Tabla ICE automática: Q, sentido y concentraciones de equilibrio") + Z.seg(sg, Object.keys(EQS).map(function (q) { return [q, sub(EQS[q].t)]; }), k) +
      '<div class="ranges" id="' + box + '"></div><div class="out"></div>';
    var out = r.querySelector(".out"), bx = r.querySelector("#" + box);
    function set() {
      var E = EQS[k]; bx.innerHTML = Z.fl(iK, "K<sub>c</sub>", String(E.K).replace(".", ",")) + E.sp.map(function (s, i) { return Z.fl(iK + "c" + i, "[" + sub(s) + "]₀ (M)", String(E.c0[i]).replace(".", ",")); }).join(""); draw();
    }
    function draw() {
      var E = EQS[k], K = Z.val(r, iK), c = E.sp.map(function (s, i) { return Z.val(r, iK + "c" + i); });
      if (!(K > 0) || c.some(function (x) { return !(x >= 0); })) { out.innerHTML = '<p class="err">K debe ser positiva y las concentraciones, no negativas.</p>'; return; }
      var lo = -Infinity, hi = Infinity;
      E.nu.forEach(function (n, i) { if (n < 0) hi = Math.min(hi, c[i] / -n); else lo = Math.max(lo, -c[i] / n); });
      var lnQ = function (x) { var s = 0; E.nu.forEach(function (n, i) { s += n * Math.log(Math.max(c[i] + n * x, 1e-300)); }); return s; };
      var canF = c.every(function (x, i) { return E.nu[i] > 0 || x > 0; }), canB = c.every(function (x, i) { return E.nu[i] < 0 || x > 0; });
      if (!canF && !canB) { out.innerHTML = '<p class="err">Falta al menos un reactivo y al menos un producto: la mezcla no puede reaccionar en ningún sentido.</p>'; return; }
      var Q = !canB ? 0 : !canF ? Infinity : Math.exp(lnQ(0)), sentido = !canB ? "→ hacia productos (aún no hay productos)" : !canF ? "← hacia reactivos (falta un reactivo)" : Q < K ? "→ hacia productos (Q &lt; K)" : Q > K ? "← hacia reactivos (Q &gt; K)" : "ya está en equilibrio";
      var x = biseccion(function (z) { return lnQ(z) - Math.log(K); }, lo + 1e-12 * (hi - lo), hi - 1e-12 * (hi - lo));
      var fila = function (lab, f) { return [lab].concat(E.sp.map(function (s, i) { return f(i); })); };
      out.innerHTML = '<div class="eq">' + sub(E.t) + "</div>" + Z.res([["Q inicial", isFinite(Q) ? Z.sci(Q, 3) : "∞"], ["K<sub>c</sub>", Z.sci(K, 3)], ["Sentido", sentido], ["Avance x", Z.sci(x, 4) + " M"]]) +
        Z.tabla(["", ].concat(E.sp.map(sub)), [fila("I", function (i) { return Z.fx(c[i], 4); }), fila("C", function (i) { var n = E.nu[i]; return (n > 0 ? "+" : "−") + (Math.abs(n) === 1 ? "" : Math.abs(n)) + "x"; }), { cls: "on", c: fila("E", function (i) { return Z.sci(c[i] + E.nu[i] * x, 4); }) }]) +
        Z.nota("Si Q &lt; K la reacción avanza hacia productos (x &gt; 0); si Q &gt; K retrocede (x &lt; 0). La herramienta resuelve la ecuación exacta, sin aproximaciones: compara con tu resultado usando «x pequeño».");
    }
    Z.wireSeg(r, sg, function (q) { k = q; set(); }); Z.on(r, "input", draw); set();
  };

  /* ---------- I2 · pH de ácidos y bases ---------- */
  T.ph = function (r) {
    var sg = Z.uid("t"), iC = Z.uid("C"), iK = Z.uid("K"), k = "ad";
    var TP = { af: "Ácido fuerte", bf: "Base fuerte", ad: "Ácido débil", bd: "Base débil" };
    r.innerHTML = Z.head("Ácido-base", "pH de un ácido o una base en agua") + Z.seg(sg, Object.keys(TP).map(function (q) { return [q, TP[q]]; }), k) +
      '<div class="ranges">' + Z.fl(iC, "Concentración C (M)", "0,10") + Z.fl(iK, "Kₐ o K<sub>b</sub> (solo débiles)", "1,8e-5") + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function draw() {
      var C = Z.val(r, iC), K = parseFloat(String(r.querySelector("#" + iK).value).replace(",", ".")), Kw = 1e-14;
      if (!(C > 0)) { out.innerHTML = '<p class="err">C debe ser positiva.</p>'; return; }
      var x, aprox = null, pct = null;
      if (k === "af" || k === "bf") x = (C + Math.sqrt(C * C + 4 * Kw)) / 2;
      else {
        if (!(K > 0)) { out.innerHTML = '<p class="err">Ingresa Kₐ o K<sub>b</sub> positiva (puedes escribir 1,8e-5).</p>'; return; }
        x = (-K + Math.sqrt(K * K + 4 * K * C)) / 2; aprox = Math.sqrt(K * C); pct = 100 * x / C;
      }
      var acido = k === "af" || k === "ad", H = acido ? x : Kw / x, pH = -Math.log10(H);
      var it = [["[" + (acido ? "H₃O⁺" : "OH⁻") + "]", Z.sci(x, 3) + " M"], ["pH", Z.fx(pH, 2)], ["pOH", Z.fx(14 - pH, 2)]];
      if (aprox !== null) it.push(["Con la aproximación √(K·C)", Z.sci(aprox, 3) + " M"], ["% de ionización", Z.fx(pct, 2) + " %" + (pct < 5 ? " (aproximación válida)" : " (> 5 %: usa la cuadrática)")]);
      out.innerHTML = Z.res(it) + (aprox !== null ? '<div class="eq">' + (acido ? "Kₐ" : "K<sub>b</sub>") + " = x² / (C − x)  ⇒  x = (−K + √(K² + 4KC)) / 2</div>" : '<div class="eq">' + (acido ? "[H₃O⁺]" : "[OH⁻]") + " = C (disociación completa)</div>") +
        Z.nota("A 25 °C: pH + pOH = 14 y Kₐ·K<sub>b</sub> = K<sub>w</sub> = 1,0·10⁻¹⁴ para un par conjugado. La aproximación x ≪ C se acepta si la ionización es menor que 5 %.");
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Curva de titulación ---------- */
  function phMezcla(Ca, Va, Ka, Cb, Vb) {   // ácido HA (Ka; fuerte si Ka grande) + NaOH: balance de cargas exacto
    var Vt = Va + Vb, CT = Ca * Va / Vt, Na = Cb * Vb / Vt, Kw = 1e-14;
    var f = function (lh) { var h = Math.pow(10, lh); return h + Na - Kw / h - CT * Ka / (Ka + h); };
    return -biseccion(f, -14.5, 1, 120);
  }
  T.titulacion = function (r) {
    var sg = Z.uid("t"), iCa = Z.uid("Ca"), iVa = Z.uid("Va"), iK = Z.uid("Ka"), iCb = Z.uid("Cb"), iV = Z.uid("V"), k = "debil";
    r.innerHTML = Z.head("Ácido-base", "Titulación de un ácido con NaOH") + Z.seg(sg, [["fuerte", "Ácido fuerte (HCl)"], ["debil", "Ácido débil (HA)"]], k) +
      '<div class="ranges">' + Z.fl(iCa, "C del ácido (M)", "0,10") + Z.fl(iVa, "V del ácido (mL)", "25") + Z.fl(iK, "Kₐ (si es débil)", "1,8e-5") + Z.fl(iCb, "C del NaOH (M)", "0,10") + Z.rng(iV, "NaOH agregado (mL)", 0, 50, 0.5, 12.5) + '</div><div class="two"><div class="stage"></div><div class="out"></div></div>';
    var st = r.querySelector(".stage"), out = r.querySelector(".out");
    function draw() {
      var Ca = Z.val(r, iCa), Va = Z.val(r, iVa), Ka = k === "fuerte" ? 1e8 : parseFloat(String(r.querySelector("#" + iK).value).replace(",", ".")), Cb = Z.val(r, iCb), Vb = Z.val(r, iV); Z.out(r, iV, Z.fx(Vb, 1) + " mL");
      if (!(Ca > 0 && Va > 0 && Cb > 0 && Ka > 0)) { out.innerHTML = '<p class="err">Ingresa valores positivos.</p>'; st.innerHTML = ""; return; }
      var Veq = Ca * Va / Cb, Vmax = Math.max(50, Veq * 2), pl = new Z.Plot({ x0: 0, x1: Vmax, y0: 0, y1: 14, W: 380, H: 300, aria: "Curva de titulación" }).grid(Vmax / 10, 1, { x: Vmax / 5, y: 2 });
      pl.f(function (v) { return phMezcla(Ca, Va, Ka, Cb, v); }, "ln-a", 0, Vmax, 300);
      var pH = phMezcla(Ca, Va, Ka, Cb, Vb), pHeq = phMezcla(Ca, Va, Ka, Cb, Veq);
      pl.seg(Veq, 0, Veq, 14, "ln-w dash", 1.2).pt(Vb, pH, "fok", Z.fx(pH, 2)).pt(Veq, pHeq, "", "eq.");
      if (k === "debil") pl.pt(Veq / 2, phMezcla(Ca, Va, Ka, Cb, Veq / 2), "fs", "pKa", 8, 14);
      st.innerHTML = pl.svg();
      var zona = Vb === 0 ? "inicio: solo ácido" : Vb < Veq - 1e-9 ? (k === "debil" ? "zona amortiguadora (HA/A⁻)" : "ácido en exceso") : Math.abs(Vb - Veq) < 1e-9 ? "punto de equivalencia" : "NaOH en exceso";
      out.innerHTML = Z.res([["pH con " + Z.fx(Vb, 1) + " mL", Z.fx(pH, 2)], ["Zona", zona], ["Volumen de equivalencia", Z.fx(Veq, 2) + " mL"], ["pH en la equivalencia", Z.fx(pHeq, 2)]].concat(k === "debil" ? [["pKₐ (pH a media titulación)", Z.fx(-Math.log10(Ka), 2)]] : [])) +
        Z.nota(k === "debil" ? "Ácido débil: en la equivalencia queda A⁻ (base conjugada) y el pH es <b>mayor que 7</b>. A media titulación [HA] = [A⁻] y pH = pKₐ." : "Ácido fuerte con base fuerte: en la equivalencia solo queda NaCl y el pH es 7.");
    }
    Z.wireSeg(r, sg, function (q) { k = q; draw(); }); Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Amortiguadores ---------- */
  T.buffer = function (r) {
    var ipK = Z.uid("pK"), iHA = Z.uid("HA"), iA = Z.uid("A"), iAdd = Z.uid("add");
    r.innerHTML = Z.head("Ácido-base", "Amortiguador: Henderson-Hasselbalch y adición de ácido o base") +
      '<div class="ranges">' + Z.fl(ipK, "pKₐ", "4,74") + Z.fl(iHA, "Moles de HA", "0,10") + Z.fl(iA, "Moles de A⁻", "0,10") + Z.rng(iAdd, "Se agrega (mol): − HCl · + NaOH", -0.12, 0.12, 0.005, 0.01) + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function draw() {
      var pK = Z.val(r, ipK), nHA = Z.val(r, iHA), nA = Z.val(r, iA), d = Z.val(r, iAdd); Z.out(r, iAdd, (d >= 0 ? "+" : "−") + Z.fx(Math.abs(d), 3) + (d >= 0 ? " NaOH" : " HCl"));
      if (!(nHA > 0 && nA > 0)) { out.innerHTML = '<p class="err">Necesitas moles positivos de HA y de A⁻.</p>'; return; }
      var p0 = pK + Math.log10(nA / nHA), HA2 = nHA - d, A2 = nA + d, txt;
      if (HA2 > 0 && A2 > 0) txt = Z.fx(pK + Math.log10(A2 / HA2), 2);
      else txt = "se superó la capacidad: " + (HA2 <= 0 ? "sobra base fuerte (" + Z.fx(-HA2, 3) + " mol de OH⁻)" : "sobra ácido fuerte (" + Z.fx(-A2, 3) + " mol de H₃O⁺)");
      out.innerHTML = '<div class="eq">pH = pKₐ + log([A⁻]/[HA])</div>' + Z.res([["pH inicial", Z.fx(p0, 2)], ["Tras agregar", (d >= 0 ? "OH⁻ + HA → A⁻ + H₂O" : "H₃O⁺ + A⁻ → HA + H₂O")], ["Moles nuevos", "HA = " + Z.fx(HA2, 3) + " · A⁻ = " + Z.fx(A2, 3)], ["pH final", txt]]) +
        Z.nota("Con moles (o concentraciones en el mismo volumen) da lo mismo: el volumen se cancela en el cociente. El amortiguador funciona mejor con pH = pKₐ ± 1 y resiste más mientras más moles de HA y A⁻ tenga.");
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Nernst, ΔG y K ---------- */
  T.nernst = function (r) {
    var iE = Z.uid("E"), in_ = Z.uid("n"), iQ = Z.uid("Q"), iT = Z.uid("T");
    r.innerHTML = Z.head("Electroquímica", "Ecuación de Nernst, ΔG° y K") +
      '<div class="ranges">' + Z.fl(iE, "E°<sub>celda</sub> (V)", "1,10") + Z.fl(in_, "Electrones transferidos n", "2") + Z.rng(iQ, "log Q", -6, 6, 0.1, 2) + Z.fl(iT, "T (K)", "298,15") + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function draw() {
      var E0 = Z.val(r, iE), n = Z.val(r, in_), lq = Z.val(r, iQ), Tk = Z.val(r, iT); Z.out(r, iQ, "Q = " + Z.sci(Math.pow(10, lq), 2));
      if (!(n > 0 && Tk > 0)) { out.innerHTML = '<p class="err">n y T deben ser positivos.</p>'; return; }
      var E = E0 - R_ * Tk / (n * F_) * Math.log(10) * lq, G0 = -n * F_ * E0 / 1000, G = -n * F_ * E / 1000, lK = n * F_ * E0 / (R_ * Tk * Math.log(10));
      out.innerHTML = '<div class="eq">E = E° − (RT/nF) ln Q  ≈  E° − (0,0592/n) log Q   (25 °C)</div>' +
        Z.res([["E de la celda", Z.fx(E, 4) + " V"], ["ΔG°", Z.fx(G0, 1) + " kJ/mol"], ["ΔG", Z.fx(G, 1) + " kJ/mol"], ["K", "10<sup>" + Z.fx(lK, 1) + "</sup>"], ["¿Espontánea?", E > 0 ? "sí (E &gt; 0, ΔG &lt; 0)" : E < 0 ? "no (funciona al revés)" : "equilibrio (pila agotada)"]]) +
        Z.nota("Cuando la pila se descarga, Q aumenta y E baja hasta 0: en ese punto Q = K. Una pila de concentración tiene E° = 0 y funciona solo por la diferencia de concentraciones.");
    }
    Z.on(r, "input", draw); draw();
  };

  /* ---------- I2 · Electrólisis (Faraday) ---------- */
  T.faraday = function (r) {
    var iI = Z.uid("I"), it = Z.uid("t"), in_ = Z.uid("n"), iM = Z.uid("M");
    r.innerHTML = Z.head("Electroquímica", "Electrólisis: masa depositada con la ley de Faraday") +
      '<div class="ranges">' + Z.rng(iI, "Corriente I (A)", 0.1, 20, 0.1, 2) + Z.rng(it, "Tiempo (min)", 1, 240, 1, 60) + Z.fl(in_, "Electrones por ion (n)", "2") + Z.fl(iM, "Masa molar del metal (g/mol)", "63,55") + '</div><div class="out"></div>';
    var out = r.querySelector(".out");
    function draw() {
      var I = Z.val(r, iI), tm = Z.val(r, it), n = Z.val(r, in_), M = Z.val(r, iM); Z.out(r, iI, Z.fx(I, 1) + " A"); Z.out(r, it, tm + " min");
      if (!(n > 0 && M > 0)) { out.innerHTML = '<p class="err">n y la masa molar deben ser positivos.</p>'; return; }
      var Q = I * tm * 60, ne = Q / F_, nm = ne / n, m = nm * M;
      out.innerHTML = '<div class="eq">m = (I · t · M) / (n · F)</div>' + Z.res([["Carga Q = I·t", Z.fx(Q, 0) + " C"], ["Moles de electrones", Z.fx(ne, 5) + " mol"], ["Moles de metal", Z.fx(nm, 5) + " mol"], ["Masa depositada", Z.fx(m, 4) + " g"]]) +
        Z.nota("El tiempo va en segundos. F = 96 485 C por mol de electrones. Para Cu²⁺ + 2e⁻ → Cu, n = 2; para Ag⁺ + e⁻ → Ag, n = 1.");
    }
    Z.on(r, "input", draw); draw();
  };
