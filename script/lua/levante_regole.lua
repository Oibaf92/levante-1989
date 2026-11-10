--[[
  LEVANTE 1989 - registrazioni per le regole speciali della campagna (README)

  Annota in LEVANTE.extra (salvato nello stato) cio' che serve all'arbitro per:
  - CSAR: eiezioni (posizione, terra/mare) e piloti recuperati (un elicottero della stessa parte
    atterra entro RAGGIO_CSAR m da un pilota a terra: LEVANTE_PILOTI = { ["nome"] = {x=, y=, coal=} });
  - AIM-54 contati: lanci per coalizione;
  - contro-artiglieria (AN/TPQ-37): tiri dei gruppi di artiglieria/lanciarazzi (LEVANTE_ARTIGLIERIA);
  - ricognizione TARPS: traccia dei voli con il pod (LEVANTE_TARPS = { ["gruppo"] = true }) sotto i
    20.000 ft, ogni TARPS_PASSO s, e se l'aereo atterra.
  Il calcolo delle conseguenze (intel, scorte, piloti) lo fa l'arbitro all'importazione (esiti.py).
  Script leggero: eventi + un timer ogni TARPS_PASSO s solo se ci sono voli TARPS.
  Richiede levante_core.lua.
]]

local ART = LEVANTE_ARTIGLIERIA or {}
local TARPS = LEVANTE_TARPS or {}
local PILOTI = LEVANTE_PILOTI or {}
local RAGGIO_CSAR = 300
local TARPS_PASSO, TARPS_QUOTA = 10, 6096

LEVANTE.extra = LEVANTE.extra or {}
local X = LEVANTE.extra
X.eiezioni = X.eiezioni or {}
X.aim54 = X.aim54 or { [1] = 0, [2] = 0 }
X.tiri = X.tiri or {}
X.tarps = X.tarps or {}
X.csar = X.csar or {}

local function log(msg) env.info("[LEVANTE REGOLE] " .. msg) end
local function ora() return LEVANTE.orologio and LEVANTE.orologio() or "" end

local gestore = {}
function gestore:onEvent(e)
  local ok, err = pcall(function()
    local u = e.initiator
    if e.id == world.event.S_EVENT_EJECTION and u then
      local p = u:getPoint()
      local s = land.getSurfaceType({ x = p.x, y = p.z })
      X.eiezioni[#X.eiezioni + 1] = { nome = u:getName(), tipo = u:getTypeName(), coal = u:getCoalition(),
        gruppo = u:getGroup() and u:getGroup():getName() or "", x = p.x, y = p.z, ora = ora(),
        mare = (s == land.SurfaceType.WATER or s == land.SurfaceType.SHALLOW_WATER),
        giocatore = u:getPlayerName() }
    elseif e.id == world.event.S_EVENT_SHOT and e.weapon then
      local arma = e.weapon:getTypeName() or ""
      if string.find(arma, "AIM_54", 1, true) and u then
        local c = u:getCoalition()
        X.aim54[c] = (X.aim54[c] or 0) + 1
      end
      local g = u and u.getGroup and u:getGroup()
      if g and ART[g:getName()] then
        local p = u:getPoint()
        X.tiri[#X.tiri + 1] = { gruppo = g:getName(), x = p.x, y = p.z, ora = ora() }
      end
    elseif e.id == world.event.S_EVENT_SHOOTING_START and u then
      local g = u.getGroup and u:getGroup()
      if g and ART[g:getName()] then
        local p = u:getPoint()
        X.tiri[#X.tiri + 1] = { gruppo = g:getName(), x = p.x, y = p.z, ora = ora() }
      end
    elseif e.id == world.event.S_EVENT_LAND and u then
      local g = u.getGroup and u:getGroup()
      if g and TARPS[g:getName()] then
        X.tarps[u:getName()] = X.tarps[u:getName()] or { punti = {} }
        X.tarps[u:getName()].atterrato = true
      end
      -- soccorso: elicottero amico atterrato vicino a un pilota a terra
      local okd, desc = pcall(function() return u:getDesc() end)
      if okd and desc and desc.category == Unit.Category.HELICOPTER then
        local p = u:getPoint()
        for nome, pil in pairs(PILOTI) do
          if pil.coal == u:getCoalition() and not X.csar[nome]
             and math.sqrt((pil.x - p.x) ^ 2 + (pil.y - p.z) ^ 2) < RAGGIO_CSAR then
            X.csar[nome] = { da = u:getName(), ora = ora() }
            trigger.action.outTextForCoalition(u:getCoalition(), "Pilota " .. nome .. " recuperato!", 15)
            local gp = Group.getByName("Pilota " .. nome)
            if gp then gp:destroy() end
            if LEVANTE.salva then LEVANTE.salva("pilota_recuperato") end
          end
        end
      end
    end
  end)
  if not ok then log("errore: " .. tostring(err)) end
end
world.addEventHandler(gestore)

-- traccia dei voli TARPS
local function traccia()
  for nome_g in pairs(TARPS) do
    local g = Group.getByName(nome_g)
    if g and g:isExist() then
      for _, u in ipairs(g:getUnits() or {}) do
        if u:isExist() and u:inAir() then
          local p = u:getPoint()
          if p.y < TARPS_QUOTA then
            local t = X.tarps[u:getName()] or { punti = {} }
            t.punti[#t.punti + 1] = { x = math.floor(p.x), y = math.floor(p.z) }
            X.tarps[u:getName()] = t
          end
        end
      end
    end
  end
  return timer.getTime() + TARPS_PASSO
end
if next(TARPS) then timer.scheduleFunction(function() return traccia() end, nil, timer.getTime() + TARPS_PASSO) end

-- AIM-54 nel magazzino della portaerei (se l'API dei magazzini lo consente; altrimenti solo il carico iniziale)
if LEVANTE_AIM54 then
  local ok, err = pcall(function()
    local ab = Airbase.getByName(LEVANTE_AIM54.nave)
    local wh = ab and ab.getWarehouse and ab:getWarehouse()
    if wh and wh.setItem then
      wh:setItem("weapons.missiles.AIM_54C_Mk47", LEVANTE_AIM54.scorta)
      log("magazzino " .. LEVANTE_AIM54.nave .. ": AIM-54C " .. LEVANTE_AIM54.scorta)
    end
  end)
  if not ok then log("magazzino AIM-54 non impostato: " .. tostring(err)) end
end
log("caricato")
