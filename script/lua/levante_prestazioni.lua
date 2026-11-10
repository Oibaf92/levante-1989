--[[
  LEVANTE 1989 - prestazioni: rimozione degli aerei IA rientrati

  Un aereo IA che ha finito la missione (motori spenti dopo l'atterraggio, o atterrato da
  RIMOZIONE_DOPO secondi) viene tolto dalla missione: non serve piu' e pesa sulla CPU.
  I gruppi del giocatore (LEVANTE_GIOCATORE = { ["nome gruppo"] = true }) non si toccano.
  Gli aerei rimossi sono annotati in LEVANTE.extra.rientrati: per la campagna sono rientrati
  alla base, NON perdite (vedi script/tools/esiti.py).
  Regole per script leggeri: solo eventi, un timer per aereo atterrato.
  Richiede levante_core.lua.
]]

local GIOCATORE = LEVANTE_GIOCATORE or {}
local RIMOZIONE_DOPO = 180          -- s dopo l'atterraggio, se i motori non si spengono prima

LEVANTE.extra = LEVANTE.extra or {}
LEVANTE.extra.rientrati = LEVANTE.extra.rientrati or {}
local RIENTRATI = LEVANTE.extra.rientrati

local function log(msg) env.info("[LEVANTE PRESTAZIONI] " .. msg) end

local function rimuovibile(u)
  if not u or not u:isExist() then return false end
  local cat = u:getDesc().category
  if cat ~= Unit.Category.AIRPLANE and cat ~= Unit.Category.HELICOPTER then return false end
  if u:getPlayerName() then return false end
  local g = u:getGroup()
  if not g or GIOCATORE[g:getName()] then return false end
  return true
end

local function rimuovi(nome)
  local u = Unit.getByName(nome)
  if not u or not u:isExist() or u:inAir() then return end
  RIENTRATI[nome] = LEVANTE.orologio and LEVANTE.orologio() or true
  u:destroy()
  log("rimosso (rientrato): " .. nome)
  if LEVANTE.debug then LEVANTE.debug(nome .. ": rientrato, rimosso dalla missione") end
end

local gestore = {}
function gestore:onEvent(e)
  if e.id ~= world.event.S_EVENT_LAND and e.id ~= world.event.S_EVENT_ENGINE_SHUTDOWN then return end
  local ok, err = pcall(function()
    local u = e.initiator
    if not rimuovibile(u) then return end
    local nome = u:getName()
    local ritardo = (e.id == world.event.S_EVENT_ENGINE_SHUTDOWN) and 10 or RIMOZIONE_DOPO
    timer.scheduleFunction(function() pcall(rimuovi, nome) end, nil, timer.getTime() + ritardo)
  end)
  if not ok then log("errore: " .. tostring(err)) end
end
world.addEventHandler(gestore)
log("caricato")
