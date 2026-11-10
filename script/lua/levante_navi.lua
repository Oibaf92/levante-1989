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
      prue vicine (fino a +-40 gradi).

  Dati: LEVANTE_NAVI = { ["nome gruppo"] = { vento_ponte_kt=, min_kt=, max_kt=, scarto=, tratta_nm=, comandi={...} }, ... }
  Usa LEVANTE.annota se presente (levante_core.lua).
]]

local NAVI = LEVANTE_NAVI or {}
local KT = 0.514444
local NM = 1852
local RIPIANIFICA = 1800       -- s

local function log(msg) env.info("[LEVANTE NAVI] " .. msg) end

local function inMare(x, z)
  local s = land.getSurfaceType({ x = x, y = z })
  return s == land.SurfaceType.WATER or s == land.SurfaceType.SHALLOW_WATER
end

-- lunghezza (m) percorribile in mare lungo una prua, a passi di 2 km, fino a 'massimo'
local function acquaLibera(x, z, prua, massimo)
  local dx, dz = math.cos(prua), math.sin(prua)
  local d = 0
  while d < massimo do
    local nd = d + 2000
    if not inMare(x + dx * nd, z + dz * nd) then return d end
    d = nd
  end
  return massimo
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
  if da then
    prua = da + math.rad(cfg.scarto or 0)
  else
    local pos = capo:getPosition()                        -- calma: si mantiene la prua attuale
    prua = math.atan2(pos.x.z, pos.x.x)
  end
  local vel_kt = math.max(cfg.min_kt or 10, math.min(cfg.max_kt or 30, (cfg.vento_ponte_kt or 25) - vel / KT))
  local tratta = (cfg.tratta_nm or 60) * NM
  local migliore, lunga = prua, acquaLibera(p.x, p.z, prua, tratta)
  if lunga < tratta * 0.5 then
    for _, delta in ipairs({ 10, -10, 20, -20, 30, -30, 40, -40 }) do
      local pr = prua + math.rad(delta)
      local l = acquaLibera(p.x, p.z, pr, tratta)
      if l > lunga + 4000 then migliore, lunga = pr, l end
      if l >= tratta * 0.5 then break end
    end
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
  log(string.format("%s: prua %03d, %d nodi, vento da %s a %.0f nodi, tratta %.0f nm", nome, gradi, math.floor(vel_kt + 0.5),
    da and string.format("%03d", math.floor((math.deg(da) % 360) + 0.5)) or "---", vel / KT, lunga / NM))
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
