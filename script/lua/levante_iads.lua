--[[
  LEVANTE 1989 - rete di difesa aerea (IADS) senza onniscienza

  Progetto approvato dal giocatore (docs/lezioni.md):
  - i radar di tiro dei SAM stanno SPENTI e si accendono solo quando la rete segnala un bersaglio
    dentro la loro portata, per il tempo necessario;
  - la rete "vede" solo cio' che i suoi sensori rilevano davvero (getDetectedTargets): radar di
    sorveglianza, AWACS, SAM gia' accesi, osservatori a terra a vista. DCS calcola orizzonte radar e
    rilievo: chi vola basso dietro le montagne non viene visto;
  - se i sensori della rete sono distrutti le batterie sono cieche: ogni tanto accendono il proprio
    radar per cercare (esponendosi agli HARM);
  - l'allarme arriva alla batteria con un ritardo; l'AWACS condivide solo in parte, con piu' ritardo;
  - reazione ai missili antiradar incerta: la batteria bersaglio spegne con probabilita' P_HARM dopo
    qualche secondo; le batterie vicine con probabilita' minore;
  - i SAM mobili (SA-6, SA-8, Hawk) dopo aver sparato si spostano di 0,8-1,5 km a radar spento.
  Regole per script leggeri: un solo ciclo ogni CICLO secondi, eventi per tiri e lanci.

  Dati (dal costruttore):
  LEVANTE_IADS = { [coalizione] = {
      sam = { ["gruppo"] = { tipo = "sa6", portata = m, mobile = true }, ... },
      sensori = { ["gruppo EWR"] = "radar", ["gruppo AWACS"] = "awacs", ["gruppo carri"] = "vista", ... } } }
  Richiede levante_core.lua.
]]

local DATI = LEVANTE_IADS or {}
local CICLO = 10                 -- s tra due controlli della rete
local RITARDO_RETE = 8           -- s dall'avvistamento alla batteria
local RITARDO_AWACS = 20         -- s in piu' per i dati dell'AWACS
local P_AWACS = 0.7              -- probabilita' che una traccia AWACS venga passata alla rete
local ATTIVAZIONE = 0.85         -- frazione della portata entro cui la batteria si accende
local TENUTA = 45                -- s di radar acceso dopo l'ultimo bersaglio in portata
local P_HARM, P_HARM_VICINE = 0.65, 0.3
local SPENTO_HARM = { 60, 120 }  -- s di silenzio dopo un antiradar
local RICERCA_OGNI, RICERCA_DURATA = 300, 30   -- batteria cieca: ricerca autonoma
local ANTIRADAR = { "AGM_88", "AGM_45", "AGM_122", "Kh-58", "Kh-25MP", "X_58", "X_25MP", "AGM-88", "AGM-45" }

local S = {}   -- stato per coalizione: batterie, tracce
local function log(msg) env.info("[LEVANTE IADS] " .. msg) end

local function gruppoVivo(nome)
  local g = Group.getByName(nome)
  if g and g:isExist() and g:getSize() > 0 then return g end
  return nil
end

local function centro(g)
  local sx, sz, n = 0, 0, 0
  for _, u in ipairs(g:getUnits() or {}) do
    local p = u:getPoint()
    sx, sz, n = sx + p.x, sz + p.z, n + 1
  end
  if n == 0 then return nil end
  return { x = sx / n, z = sz / n }
end

local function radar(nome, acceso)
  local g = gruppoVivo(nome)
  if not g then return end
  if g.enableEmission then
    pcall(function() g:enableEmission(acceso) end)
  end
  local c = g:getController()
  c:setOption(AI.Option.Ground.id.ALARM_STATE,
    acceso and AI.Option.Ground.val.ALARM_STATE.RED or AI.Option.Ground.val.ALARM_STATE.GREEN)
end

------------------------------------------------------------------------
-- Sensori della rete: solo bersagli realmente rilevati
------------------------------------------------------------------------
local function raccogliTracce(coal, st, ora)
  local nemico = (coal == 1) and 2 or 1
  local function aggiungi(obj, ritardo)
    if not obj or not obj.isExist or not obj:isExist() then return end
    local ok, c = pcall(function() return obj:getCoalition() end)
    if not ok or c ~= nemico then return end
    local okc, cat = pcall(function() return obj:getDesc().category end)
    if not okc or (cat ~= Unit.Category.AIRPLANE and cat ~= Unit.Category.HELICOPTER) then return end
    local p = obj:getPoint()
    local id = obj:getName()
    local t = st.tracce[id]
    local pronto = ora + ritardo
    if t and t.pronto < pronto then pronto = t.pronto end
    st.tracce[id] = { x = p.x, y = p.y, z = p.z, visto = ora, pronto = pronto }
  end
  local quanti = 0
  for nome, ruolo in pairs(DATI[coal].sensori or {}) do
    local g = gruppoVivo(nome)
    if g then
      quanti = quanti + 1
      local u = g:getUnit(1)
      if u then
        local ok, rilevati = pcall(function()
          if ruolo == "vista" then
            return u:getController():getDetectedTargets(Controller.Detection.VISUAL, Controller.Detection.OPTIC)
          end
          return u:getController():getDetectedTargets(Controller.Detection.RADAR)
        end)
        if ok and rilevati then
          for _, r in pairs(rilevati) do
            if ruolo ~= "awacs" or math.random() < P_AWACS then
              aggiungi(r.object, RITARDO_RETE + (ruolo == "awacs" and RITARDO_AWACS or 0))
            end
          end
        end
      end
    end
  end
  -- i SAM gia' accesi sono sensori anche loro (senza ritardo per se stessi, con ritardo per gli altri)
  for nome, b in pairs(st.batterie) do
    if b.acceso then
      local g = gruppoVivo(nome)
      local u = g and g:getUnit(1)
      if u then
        local ok, rilevati = pcall(function() return u:getController():getDetectedTargets(Controller.Detection.RADAR) end)
        if ok and rilevati then
          for _, r in pairs(rilevati) do aggiungi(r.object, RITARDO_RETE) end
        end
      end
    end
  end
  -- tracce vecchie
  for id, t in pairs(st.tracce) do
    if ora - t.visto > 3 * CICLO then st.tracce[id] = nil end
  end
  st.sensoriVivi = quanti
end

------------------------------------------------------------------------
-- Ciclo della rete
------------------------------------------------------------------------
local function ciclo(coal, ora)
  local st = S[coal]
  raccogliTracce(coal, st, ora)
  for nome, b in pairs(st.batterie) do
    local g = gruppoVivo(nome)
    if not g then
      st.batterie[nome] = nil
    elseif ora >= (b.silenzioFino or 0) and not b.inMovimento then
      local c = centro(g)
      local inPortata = false
      if c then
        for _, t in pairs(st.tracce) do
          if t.pronto <= ora and math.sqrt((t.x - c.x) ^ 2 + (t.z - c.z) ^ 2) < b.portata * ATTIVAZIONE then
            inPortata = true
            break
          end
        end
      end
      if inPortata then
        b.ultimoBersaglio = ora
        if not b.acceso then radar(nome, true); b.acceso = true end
      elseif b.acceso and ora - (b.ultimoBersaglio or 0) > TENUTA and ora >= (b.ricercaFino or 0) then
        radar(nome, false); b.acceso = false
      elseif not b.acceso and st.sensoriVivi == 0 and ora - (b.ultimaRicerca or -1e9) > RICERCA_OGNI then
        -- rete cieca: breve ricerca con il proprio radar
        b.ultimaRicerca, b.ricercaFino = ora, ora + RICERCA_DURATA
        radar(nome, true); b.acceso = true
      end
    end
  end
end

------------------------------------------------------------------------
-- Antiradar e spostamento dopo il tiro
------------------------------------------------------------------------
local function eAntiradar(arma)
  local ok, nome = pcall(function() return arma:getTypeName() end)
  if not ok or not nome then return false end
  for _, k in ipairs(ANTIRADAR) do
    if string.find(nome, k, 1, true) then return true end
  end
  return false
end

local function silenzio(nome, b, ora)
  timer.scheduleFunction(function()
    radar(nome, false)
    b.acceso = false
    b.silenzioFino = timer.getTime() + math.random(SPENTO_HARM[1], SPENTO_HARM[2])
  end, nil, ora + math.random(3, 8))
end

local function reazioneHarm(e)
  local arma = e.weapon
  local ora = timer.getTime()
  local bersaglio = nil
  pcall(function() local t = arma:getTarget(); bersaglio = t and t:getGroup() and t:getGroup():getName() end)
  local pt = e.initiator and e.initiator:getPoint()
  for coal, st in pairs(S) do
    for nome, b in pairs(st.batterie) do
      if b.acceso then
        local p = (nome == bersaglio) and P_HARM or 0
        if p == 0 and pt then
          local g = gruppoVivo(nome)
          local c = g and centro(g)
          if c and math.sqrt((c.x - pt.x) ^ 2 + (c.z - pt.z) ^ 2) < 100000 then p = P_HARM_VICINE end
        end
        if p > 0 and math.random() < p then
          silenzio(nome, b, ora)
          LEVANTE.annota("iads_silenzio_harm", { gruppo = nome })
        end
      end
    end
  end
end

local function spostaDopoTiro(nome, b)
  if b.inMovimento then return end
  local g = gruppoVivo(nome)
  local c = g and centro(g)
  if not c then return end
  for _ = 1, 8 do
    local a, d = math.random() * 2 * math.pi, 800 + math.random() * 700
    local x, z = c.x + d * math.cos(a), c.z + d * math.sin(a)
    local s = land.getSurfaceType({ x = x, y = z })
    if s == land.SurfaceType.LAND or s == land.SurfaceType.ROAD then
      b.inMovimento = true
      radar(nome, false); b.acceso = false
      g:getController():setTask({ id = "Mission", params = { route = { points = {
        { x = c.x, y = c.z, type = "Turning Point", action = "Off Road", speed = 8 },
        { x = x, y = z, type = "Turning Point", action = "Off Road", speed = 8 },
      } } } })
      timer.scheduleFunction(function() b.inMovimento = false end, nil, timer.getTime() + d / 8 + 60)
      LEVANTE.annota("iads_spostamento", { gruppo = nome, metri = math.floor(d) })
      return
    end
  end
end

local gestore = {}
function gestore:onEvent(e)
  if e.id ~= world.event.S_EVENT_SHOT then return end
  local ok, err = pcall(function()
    if eAntiradar(e.weapon) then reazioneHarm(e) return end
    local g = e.initiator and e.initiator.getGroup and e.initiator:getGroup()
    if not g then return end
    local nome = g:getName()
    for _, st in pairs(S) do
      local b = st.batterie[nome]
      if b and b.mobile and not b.spostamentoPrevisto then
        b.spostamentoPrevisto = true
        timer.scheduleFunction(function() b.spostamentoPrevisto = false; spostaDopoTiro(nome, b) end,
          nil, timer.getTime() + 90)
      end
    end
  end)
  if not ok then log("errore evento: " .. tostring(err)) end
end
world.addEventHandler(gestore)

------------------------------------------------------------------------
-- Avvio: tutte le batterie spente
------------------------------------------------------------------------
for coal, d in pairs(DATI) do
  S[coal] = { batterie = {}, tracce = {}, sensoriVivi = 0 }
  local n = 0
  for nome, cfg in pairs(d.sam or {}) do
    S[coal].batterie[nome] = { portata = cfg.portata, mobile = cfg.mobile, acceso = false }
    pcall(radar, nome, false)
    n = n + 1
  end
  log(string.format("coalizione %d: %d batterie, radar spenti", coal, n))
end

local function giro()
  local ora = timer.getTime()
  for coal in pairs(S) do
    local ok, err = pcall(ciclo, coal, ora)
    if not ok then log("errore ciclo: " .. tostring(err)) end
  end
  return ora + CICLO
end
timer.scheduleFunction(function() return giro() end, nil, timer.getTime() + 5)
