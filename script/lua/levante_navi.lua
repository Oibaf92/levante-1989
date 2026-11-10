--[[
  LEVANTE 1989 - navi da aviazione contro vento

  Portaerei e navi d'assalto devono navigare con il vento in prua per i decolli e gli
  appontaggi. Il vento della missione puo' cambiare (meteo, versioni di DCS, convenzioni
  "da"/"verso"), quindi la rotta non si fissa nel Mission Editor: all'avvio, e poi ogni
  RIPIANIFICA secondi, questo script legge il vento reale sulla nave (atmosphere.getWind)
  e le assegna una tratta contro vento:
    - prua = direzione da cui viene il vento + scarto (ponte angolato della CVN: ~9 gradi);
    - velocita' tale che il vento sul ponte sia circa 'vento_ponte_kt' (entro min/max);
    - tratta lunga 'tratta_nm', accorciata prima della terra; se troppo corta prova
      prue vicine (fino a +-40 gradi);
    - 'minacce' (facoltativo): la tratta si ferma prima di scendere sotto 'min_m' da ciascuna minaccia
      (portaerei ad almeno 150 nm da Tartus). Se contro vento non c'e' spazio, la nave si allontana
      dalla minaccia (tratta di riposizionamento, come le portaerei vere che fanno avanti e indietro).

  Dati: LEVANTE_NAVI = { ["nome gruppo"] = { vento_ponte_kt=, min_kt=, max_kt=, scarto=, tratta_nm=, comandi={...},
                                            minacce={ {nome=, x=, z=, min_m=}, ... } }, ... }
  Usa LEVANTE.annota se presente (levante_core.lua).
]]

local NAVI = LEVANTE_NAVI or {}
local KT = 0.514444
local NM = 1852
local RIPIANIFICA = 1800       -- s
local CALMA = 3                -- m/s: sotto, la prua non segue il vento ma va lontano dalla minaccia

local function log(msg) env.info("[LEVANTE NAVI] " .. msg) end

local function inMare(x, z)
  local s = land.getSurfaceType({ x = x, y = z })
  return s == land.SurfaceType.WATER or s == land.SurfaceType.SHALLOW_WATER
end

-- margine (m) dalla minaccia piu' vicina: distanza - distanza minima (nil se non ci sono minacce)
local function margine(x, z, minacce)
  local out
  for _, m in pairs(minacce or {}) do
    local d = math.sqrt((x - m.x) ^ 2 + (z - m.z) ^ 2) - m.min_m
    if not out or d < out then out = d end
  end
  return out
end

-- lunghezza (m) percorribile lungo una prua, a passi di 2 km, fino a 'massimo': si ferma prima della
-- terra e prima di entrare (o di avanzare) dentro la distanza minima da una minaccia
local function acquaLibera(x, z, prua, massimo, minacce)
  local dx, dz = math.cos(prua), math.sin(prua)
  local d, prec = 0, margine(x, z, minacce)
  while d < massimo do
    local nd = d + 2000
    local px, pz = x + dx * nd, z + dz * nd
    if not inMare(px, pz) then return d end
    local m = margine(px, pz, minacce)
    if m and m < 0 and m < prec then return d end
    d, prec = nd, m
  end
  return massimo
end

-- prua che allontana dalla minaccia piu' vicina (nil se non ce ne sono)
local function pruaVia(x, z, minacce)
  local best, dist
  for _, m in pairs(minacce or {}) do
    local d = math.sqrt((x - m.x) ^ 2 + (z - m.z) ^ 2) - m.min_m
    if not dist or d < dist then best, dist = math.atan2(z - m.z, x - m.x), d end
  end
  return best
end

local function ventoDa(x, z)
  local v = atmosphere.getWind({ x = x, y = 20, z = z })   -- vettore verso cui soffia il vento
  local vel = math.sqrt(v.x * v.x + v.z * v.z)
  if vel < 0.5 then return nil, 0 end
  return math.atan2(-v.z, -v.x), vel                       -- direzione DA cui viene (rad, nord = x)
end

local function pianifica(nome, cfg)
  local g = Group.getByName(nome)
  if not g or not g:isExist() then return end
  local capo = g:getUnit(1)
  if not capo then return end
  local p = capo:getPoint()
  local da, vel = ventoDa(p.x, p.z)
  local prua
  if da and vel < CALMA then
    -- vento quasi assente: la nave crea da se' il vento sul ponte, quindi naviga lontano dalla minaccia
    prua = math.rad(cfg.prua_calma or 270)
  elseif da then
    prua = da + math.rad(cfg.scarto or 0)
  else
    local pos = capo:getPosition()                        -- calma: si mantiene la prua attuale
    prua = math.atan2(pos.x.z, pos.x.x)
  end
  local vel_kt = math.max(cfg.min_kt or 10, math.min(cfg.max_kt or 30, (cfg.vento_ponte_kt or 25) - vel / KT))
  local tratta = (cfg.tratta_nm or 60) * NM
  local minacce = cfg.minacce
  local migliore, lunga = prua, acquaLibera(p.x, p.z, prua, tratta, minacce)
  if lunga < tratta * 0.5 then
    for _, delta in ipairs({ 10, -10, 20, -20, 30, -30, 40, -40 }) do
      local pr = prua + math.rad(delta)
      local l = acquaLibera(p.x, p.z, pr, tratta, minacce)
      if l > lunga + 4000 then migliore, lunga = pr, l end
      if l >= tratta * 0.5 then break end
    end
  end
  local nota = ""
  if minacce and lunga < 10 * NM then
    -- contro vento si andrebbe verso la minaccia: tratta di riposizionamento lontano da essa
    local via = pruaVia(p.x, p.z, minacce)
    for _, delta in ipairs({ 0, 20, -20, 40, -40, 60, -60, 90, -90 }) do
      local pr = via + math.rad(delta)
      local l = acquaLibera(p.x, p.z, pr, tratta, minacce)
      if l > lunga then migliore, lunga = pr, l end
      if l >= 20 * NM then break end
    end
    vel_kt = cfg.max_kt or 30
    nota = " (riposizionamento lontano dalla minaccia, niente operazioni di volo)"
  end
  lunga = math.max(lunga - 3000, 2000)                     -- margine dalla costa
  local fx, fz = p.x + math.cos(migliore) * lunga, p.z + math.sin(migliore) * lunga
  local v = vel_kt * KT
  g:getController():setTask({
    id = "Mission",
    params = { route = { points = {
      { x = p.x, y = p.z, type = "Turning Point", action = "Turning Point", speed = v },
      { x = fx, y = fz, type = "Turning Point", action = "Turning Point", speed = v },
    } } },
  })
  -- TACAN/ICLS/Link4/ACLS: si riattivano dopo il cambio di rotta
  for _, c in ipairs(cfg.comandi or {}) do pcall(function() g:getController():setCommand(c) end) end
  local gradi = math.floor((math.deg(migliore) % 360) + 0.5)
  local testo = string.format("%s: prua %03d, %d nodi, vento da %s a %.0f nodi, tratta %.0f nm", nome, gradi, math.floor(vel_kt + 0.5),
    da and string.format("%03d", math.floor((math.deg(da) % 360) + 0.5)) or "---", vel / KT, lunga / NM) .. nota
  log(testo)
  if LEVANTE.debug then LEVANTE.debug(testo) end
  LEVANTE.extra = LEVANTE.extra or {}
  LEVANTE.extra.navi = LEVANTE.extra.navi or {}
  LEVANTE.extra.navi[nome] = { prua = gradi, nodi = math.floor(vel_kt + 0.5), tratta_nm = math.floor(lunga / NM) }
end

local function tutte()
  for nome, cfg in pairs(NAVI) do
    local ok, err = pcall(pianifica, nome, cfg)
    if not ok then log("errore per " .. tostring(nome) .. ": " .. tostring(err)) end
  end
  return timer.getTime() + RIPIANIFICA
end

timer.scheduleFunction(function() return tutte() end, nil, timer.getTime() + 1)
log("caricato")
