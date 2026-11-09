--[[
  LEVANTE 1989 - verifica in gioco dei piazzamenti

  Il piazzatore (Python) sceglie le posizioni sulla banca dati del terreno (griglia
  1-2 km). Questo script, all'avvio, controlla ogni veicolo sul terreno vero di DCS:
    - terra o strada (non acqua),
    - pendenza locale accettabile,
    - nessun edificio a pochi metri;
  se un veicolo non va bene lo sposta nel punto valido piu' vicino (entro 150 m) e
  ricrea il gruppo. Gli alberi non sono rilevabili: per quelli c'e' la segnalazione
  F10: un segno con scritto SPOSTA vicino a una batteria la trasferisce nella
  posizione alternativa successiva. Tutto viene annotato nello stato salvato.

  Dati in LEVANTE_PIAZZAMENTI[nome_gruppo] = {
      paese = <id>, abilita = "Good",
      unita = { {tipo=..., avanti=..., destra=..., rotta=...}, ... },   -- schema relativo
      posizioni = { {x=..., y=..., rotta=...}, ... },                    -- 1 = attuale, poi alternative
  }
  Richiede levante_core.lua.
]]

local PIAZ = LEVANTE_PIAZZAMENTI or {}
local PENDENZA_MAX = 0.15        -- 15% sui 30 m attorno al veicolo
local RAGGIO_EDIFICI = 25        -- m
local RICERCA_MAX = 150          -- m

LEVANTE.extra = LEVANTE.extra or {}
LEVANTE.extra.piazzatore = LEVANTE.extra.piazzatore or { verifiche = {}, spostamenti = {} }
local REG = LEVANTE.extra.piazzatore

local function log(msg) env.info("[LEVANTE PIAZZATORE] " .. msg) end

------------------------------------------------------------------------
local function puntoValido(x, z)
  local s = land.getSurfaceType({ x = x, y = z })
  if s ~= land.SurfaceType.LAND and s ~= land.SurfaceType.ROAD then return false end
  local h = land.getHeight({ x = x, y = z })
  local d = 15
  for _, o in ipairs({ { d, 0 }, { -d, 0 }, { 0, d }, { 0, -d } }) do
    if math.abs(land.getHeight({ x = x + o[1], y = z + o[2] }) - h) > PENDENZA_MAX * d then return false end
  end
  local n = 0
  local vol = { id = world.VolumeType.SPHERE, params = { point = { x = x, y = h, z = z }, radius = RAGGIO_EDIFICI } }
  world.searchObjects(Object.Category.SCENERY, vol, function() n = n + 1; return false end)
  return n == 0
end

local function puntoVicinoValido(x, z)
  if puntoValido(x, z) then return x, z, 0 end
  for r = 15, RICERCA_MAX, 15 do
    local n = math.max(8, math.floor(2 * math.pi * r / 15))
    for k = 0, n - 1 do
      local a = 2 * math.pi * k / n
      local px, pz = x + r * math.cos(a), z + r * math.sin(a)
      if puntoValido(px, pz) then return px, pz, r end
    end
  end
  return nil
end

local function posizioniUnita(dati, pos)
  local r = math.rad(pos.rotta)
  local cr, sr = math.cos(r), math.sin(r)
  local out = {}
  for k, u in ipairs(dati.unita) do
    out[k] = {
      tipo = u.tipo,
      x = pos.x + u.avanti * cr - u.destra * sr,
      y = pos.y + u.avanti * sr + u.destra * cr,
      rotta = (pos.rotta + u.rotta) % 360,
    }
  end
  return out
end

local function ricreaGruppo(nome, dati, unita)
  local g = { name = nome, task = "Ground Nothing", units = {} }
  for k, u in ipairs(unita) do
    g.units[k] = { name = nome .. "-" .. k, type = u.tipo, x = u.x, y = u.y,
                   heading = math.rad(u.rotta), skill = dati.abilita or "Good", playerCanDrive = false }
  end
  g.x, g.y = unita[1].x, unita[1].y
  coalition.addGroup(dati.paese, Group.Category.GROUND, g)
end

-- verifica (e correzione) di una disposizione; restituisce le unita' corrette e quante sono state spostate
local function correggi(unita)
  local spostate, scartate = 0, 0
  local out = {}
  for _, u in ipairs(unita) do
    local x, z, d = puntoVicinoValido(u.x, u.y)
    if x then
      if d > 0 then spostate = spostate + 1 end
      out[#out + 1] = { tipo = u.tipo, x = x, y = z, rotta = u.rotta }
    else
      scartate = scartate + 1
      out[#out + 1] = u          -- nessun punto valido vicino: resta dov'e' (segnalato nel registro)
    end
  end
  return out, spostate, scartate
end

------------------------------------------------------------------------
-- Verifica all'avvio
------------------------------------------------------------------------
local function verificaTutti()
  local totSpostate, totGruppi = 0, 0
  for nome, dati in pairs(PIAZ) do
    local ok, err = pcall(function()
      local g = Group.getByName(nome)
      if not g or not g:isExist() then return end
      local attuali = {}
      for k, u in ipairs(g:getUnits() or {}) do
        local p = u:getPoint()
        attuali[k] = { tipo = u:getTypeName(), x = p.x, y = p.z, rotta = 0 }
        local schema = posizioniUnita(dati, dati.posizioni[dati.attuale or 1])[k]
        if schema then attuali[k].rotta = schema.rotta end
      end
      local corrette, spostate, scartate = correggi(attuali)
      REG.verifiche[nome] = { spostate = spostate, senza_posto = scartate, unita = #attuali }
      if spostate > 0 then
        ricreaGruppo(nome, dati, corrette)
        totSpostate = totSpostate + spostate
        totGruppi = totGruppi + 1
        log(string.format("%s: %d veicoli spostati di qualche metro", nome, spostate))
      end
      if scartate > 0 then log(string.format("%s: %d veicoli senza posto valido vicino", nome, scartate)) end
    end)
    if not ok then log("errore nella verifica di " .. tostring(nome) .. ": " .. tostring(err)) end
  end
  log(string.format("verifica completata: %d veicoli spostati in %d gruppi", totSpostate, totGruppi))
end

------------------------------------------------------------------------
-- Segnalazione F10 "SPOSTA"
------------------------------------------------------------------------
local function spostaGruppo(nome, dati, motivo)
  local da = dati.posizioni[dati.attuale or 1]
  local prossimo = (dati.attuale or 1) + 1
  if not dati.posizioni[prossimo] then
    trigger.action.outText("SPOSTA: nessuna posizione alternativa rimasta per " .. nome, 15)
    return
  end
  dati.attuale = prossimo
  local unita = posizioniUnita(dati, dati.posizioni[prossimo])
  local corrette = correggi(unita)
  ricreaGruppo(nome, dati, corrette)
  REG.spostamenti[#REG.spostamenti + 1] = {
    gruppo = nome, motivo = motivo, ora = LEVANTE.orologio and LEVANTE.orologio() or "",
    da = { x = da.x, y = da.y }, a = { x = dati.posizioni[prossimo].x, y = dati.posizioni[prossimo].y },
    alternativa = prossimo,
  }
  LEVANTE.annota("piazzamento_spostato", { gruppo = nome, alternativa = prossimo })
  if LEVANTE.salva then LEVANTE.salva("piazzamento_spostato") end
  trigger.action.outText(string.format("%s spostato nella posizione alternativa %d.", nome, prossimo - 1), 15)
end

local gestore = {}
function gestore:onEvent(e)
  if e.id ~= world.event.S_EVENT_MARK_ADDED and e.id ~= world.event.S_EVENT_MARK_CHANGE then return end
  if type(e.text) ~= "string" or not string.find(string.lower(e.text), "sposta", 1, true) then return end
  local ok, err = pcall(function()
    local migliore, dmin = nil, 5000
    for nome, dati in pairs(PIAZ) do
      local g = Group.getByName(nome)
      if g and g:isExist() then
        local u = g:getUnit(1)
        if u then
          local p = u:getPoint()
          local d = math.sqrt((p.x - e.pos.x) ^ 2 + (p.z - e.pos.z) ^ 2)
          if d < dmin then migliore, dmin = nome, d end
        end
      end
    end
    if migliore then
      spostaGruppo(migliore, PIAZ[migliore], e.text)
    else
      trigger.action.outText("SPOSTA: nessuna batteria piazzata entro 5 km dal segno.", 15)
    end
  end)
  if not ok then log("errore SPOSTA: " .. tostring(err)) end
  pcall(trigger.action.removeMark, e.idx)
end
world.addEventHandler(gestore)

timer.scheduleFunction(function() verificaTutti() end, nil, timer.getTime() + 3)
log("caricato: " .. (function() local n = 0 for _ in pairs(PIAZ) do n = n + 1 end return n end)() .. " gruppi da verificare")
