--[[
  LEVANTE 1989 - motore della campagna (nucleo)

  Cosa fa:
    * verifica che MissionScripting.lua sia stato modificato (io e lfs disponibili)
    * registra gli eventi rilevanti (decolli, atterraggi, lanci, colpi, perdite,
      voti dell'LSO, ...) in un registro
    * salva una fotografia dello stato del mondo:
        - automaticamente ogni LEVANTE.autosave secondi
        - a fine missione
        - a richiesta dal menu F10
    * i file vanno in  Saved Games\DCS\Levante1989\

  I file sono tabelle Lua leggibili dagli strumenti Python della campagna.
  Non dipende da MOOSE.
]]

LEVANTE = LEVANTE or {}
LEVANTE.versione = "0.1"
LEVANTE.missione = LEVANTE.missione or "senza_nome"
LEVANTE.autosave = LEVANTE.autosave or 300
LEVANTE.registro = {}
LEVANTE.perdite = {}
LEVANTE.giocatori = {}

local function log(msg)
  env.info("[LEVANTE] " .. msg)
end

local function avviso(msg, durata)
  trigger.action.outText(msg, durata or 15)
end

------------------------------------------------------------------------
-- Accesso al disco
------------------------------------------------------------------------
LEVANTE.salvataggioAttivo = (io ~= nil and lfs ~= nil)
if LEVANTE.salvataggioAttivo then
  LEVANTE.cartella = lfs.writedir() .. "Levante1989\\"
  lfs.mkdir(LEVANTE.cartella)
end

------------------------------------------------------------------------
-- Serializzazione di tabelle Lua (chiavi ordinate, output stabile)
------------------------------------------------------------------------
local function serializza(v, rientro)
  rientro = rientro or ""
  local t = type(v)
  if t == "number" then
    if v ~= v or v == math.huge or v == -math.huge then return "0" end
    if math.floor(v) == v and math.abs(v) < 1e15 then return string.format("%d", v) end
    if math.abs(v) < 1000 then return string.format("%.6f", v) end
    return string.format("%.2f", v)
  elseif t == "string" then
    return string.format("%q", v)
  elseif t == "boolean" then
    return tostring(v)
  elseif t == "table" then
    local chiavi = {}
    for k in pairs(v) do chiavi[#chiavi + 1] = k end
    table.sort(chiavi, function(a, b)
      local ta, tb = type(a), type(b)
      if ta ~= tb then return ta < tb end
      return a < b
    end)
    local righe = {}
    local dentro = rientro .. "\t"
    for _, k in ipairs(chiavi) do
      local chiave
      if type(k) == "number" then chiave = "[" .. k .. "]" else chiave = "[" .. string.format("%q", tostring(k)) .. "]" end
      righe[#righe + 1] = dentro .. chiave .. " = " .. serializza(v[k], dentro) .. ","
    end
    return "{\n" .. table.concat(righe, "\n") .. "\n" .. rientro .. "}"
  end
  return "nil"
end
LEVANTE.serializza = serializza

function LEVANTE.scriviFile(nome, nomeTabella, tabella)
  if not LEVANTE.salvataggioAttivo then return false end
  local percorso = LEVANTE.cartella .. nome
  -- il testo viene preparato prima di aprire il file, cosi' un errore di
  -- serializzazione non lascia mai un file vuoto o troncato
  local ok, err = pcall(function()
    local testo = "-- Levante 1989 - file generato automaticamente, non modificare\n" ..
      nomeTabella .. " = " .. serializza(tabella) .. "\n"
    local f = assert(io.open(percorso, "w"))
    f:write(testo)
    f:close()
  end)
  if not ok then
    log("ERRORE scrittura " .. percorso .. ": " .. tostring(err))
    return false
  end
  return true
end

------------------------------------------------------------------------
-- Utilita'
------------------------------------------------------------------------
local function orologio(t)
  t = t or timer.getAbsTime()
  local g = math.floor(t / 86400)
  t = t - g * 86400
  return string.format("%02d:%02d:%02d", math.floor(t / 3600), math.floor(t / 60) % 60, math.floor(t) % 60)
end
LEVANTE.orologio = orologio

local function posizione(obj)
  local ok, p = pcall(function() return obj:getPoint() end)
  if not ok or not p then return nil end
  local lat, lon, alt = coord.LOtoLL(p)
  return { x = p.x, y = p.z, alt = p.y, lat = lat, lon = lon }
end

local function nomeSicuro(obj, metodo)
  if not obj then return nil end
  local ok, v = pcall(function() return obj[metodo](obj) end)
  if ok then return v end
  return nil
end

local function descriviOggetto(obj)
  if not obj then return nil end
  local d = {
    nome = nomeSicuro(obj, "getName"),
    tipo = nomeSicuro(obj, "getTypeName"),
    coalizione = nomeSicuro(obj, "getCoalition"),
    giocatore = nomeSicuro(obj, "getPlayerName"),
  }
  local ok, grp = pcall(function() return obj:getGroup() end)
  if ok and grp then d.gruppo = nomeSicuro(grp, "getName") end
  return d
end

------------------------------------------------------------------------
-- Registro eventi
------------------------------------------------------------------------
local NOMI_EVENTI = {
  [world.event.S_EVENT_SHOT] = "lancio",
  [world.event.S_EVENT_HIT] = "colpito",
  [world.event.S_EVENT_TAKEOFF] = "decollo",
  [world.event.S_EVENT_LAND] = "atterraggio",
  [world.event.S_EVENT_CRASH] = "schianto",
  [world.event.S_EVENT_EJECTION] = "eiezione",
  [world.event.S_EVENT_DEAD] = "distrutto",
  [world.event.S_EVENT_PILOT_DEAD] = "pilota_morto",
  [world.event.S_EVENT_BIRTH] = "nascita",
  [world.event.S_EVENT_ENGINE_STARTUP] = "avvio_motori",
  [world.event.S_EVENT_ENGINE_SHUTDOWN] = "spegnimento_motori",
  [world.event.S_EVENT_PLAYER_ENTER_UNIT] = "giocatore_entra",
  [world.event.S_EVENT_PLAYER_LEAVE_UNIT] = "giocatore_esce",
  [world.event.S_EVENT_REFUELING] = "rifornimento_inizio",
  [world.event.S_EVENT_REFUELING_STOP] = "rifornimento_fine",
}
if world.event.S_EVENT_LANDING_QUALITY_MARK then
  NOMI_EVENTI[world.event.S_EVENT_LANDING_QUALITY_MARK] = "voto_lso"
end
if world.event.S_EVENT_UNIT_LOST then
  NOMI_EVENTI[world.event.S_EVENT_UNIT_LOST] = "unita_persa"
end
if world.event.S_EVENT_KILL then
  NOMI_EVENTI[world.event.S_EVENT_KILL] = "abbattimento"
end
if world.event.S_EVENT_RUNWAY_TAKEOFF then
  NOMI_EVENTI[world.event.S_EVENT_RUNWAY_TAKEOFF] = "decollo_pista"
end
if world.event.S_EVENT_RUNWAY_TOUCH then
  NOMI_EVENTI[world.event.S_EVENT_RUNWAY_TOUCH] = "contatto_pista"
end

-- eventi "rumorosi" registrati solo se riguardano un giocatore
local SOLO_GIOCATORE = {
  nascita = true, avvio_motori = true, spegnimento_motori = true,
  rifornimento_inizio = true, rifornimento_fine = true,
}

function LEVANTE.annota(tipo, dati)
  dati = dati or {}
  dati.evento = tipo
  dati.t = timer.getAbsTime()
  dati.ora = orologio(dati.t)
  LEVANTE.registro[#LEVANTE.registro + 1] = dati
end

local gestore = {}
function gestore:onEvent(e)
  local ok, err = pcall(function()
    local tipo = NOMI_EVENTI[e.id]
    if not tipo then
      if e.id == world.event.S_EVENT_MISSION_END then LEVANTE.salva("fine_missione") end
      return
    end
    local chi = descriviOggetto(e.initiator)
    local coinvolgeGiocatore = (chi and chi.giocatore) or (e.target and nomeSicuro(e.target, "getPlayerName"))
    if SOLO_GIOCATORE[tipo] and not coinvolgeGiocatore then return end
    -- i lanci AI di proiettili sono troppi: registra solo armi vere o giocatori
    if tipo == "lancio" and not coinvolgeGiocatore and e.weapon then
      local desc = nomeSicuro(e.weapon, "getDesc")
      if desc and desc.category == Weapon.Category.SHELL then return end
    end
    local d = { chi = chi, pos = e.initiator and posizione(e.initiator) or nil }
    if e.target then d.bersaglio = descriviOggetto(e.target) end
    if e.weapon then d.arma = nomeSicuro(e.weapon, "getTypeName") end
    if e.weapon_name then d.arma = d.arma or e.weapon_name end
    if e.place then d.luogo = nomeSicuro(e.place, "getName") end
    if e.comment then d.commento = e.comment end
    if chi and chi.giocatore then LEVANTE.giocatori[chi.giocatore] = chi.tipo end
    if tipo == "distrutto" or tipo == "unita_persa" or tipo == "schianto" then
      if chi and chi.nome and not LEVANTE.perdite[chi.nome] then
        LEVANTE.perdite[chi.nome] = { tipo = chi.tipo, coalizione = chi.coalizione, gruppo = chi.gruppo, ora = orologio(), pos = d.pos }
      end
    end
    LEVANTE.annota(tipo, d)
    if tipo == "voto_lso" and coinvolgeGiocatore then
      avviso("LSO: " .. tostring(e.comment), 20)
    end
  end)
  if not ok then log("errore nel gestore eventi: " .. tostring(err)) end
end
world.addEventHandler(gestore)

------------------------------------------------------------------------
-- Fotografia dello stato del mondo
------------------------------------------------------------------------
local NOMI_CAT = { [0] = "aereo", [1] = "elicottero", [2] = "terra", [3] = "nave" }
local NOMI_COAL = { [0] = "neutrali", [1] = "rosso", [2] = "blu" }

function LEVANTE.fotografia()
  local stato = {
    missione = LEVANTE.missione,
    versione_motore = LEVANTE.versione,
    ora_missione = orologio(),
    t_assoluto = timer.getAbsTime(),
    t_trascorso = timer.getTime(),
    data = env.mission.date,
    gruppi = {},
    statici = {},
    perdite = LEVANTE.perdite,
    giocatori = LEVANTE.giocatori,
    extra = LEVANTE.extra,
  }
  for coal = 0, 2 do
    for cat = 0, 3 do
      for _, g in pairs(coalition.getGroups(coal, cat) or {}) do
        if g and g:isExist() then
          local gg = { nome = g:getName(), coalizione = NOMI_COAL[coal], categoria = NOMI_CAT[cat], unita = {} }
          for _, u in pairs(g:getUnits() or {}) do
            if u and u:isExist() then
              local du = {
                nome = u:getName(),
                tipo = u:getTypeName(),
                vita = u:getLife(),
                vita0 = u:getLife0(),
                attiva = u:isActive(),
                pos = posizione(u),
                giocatore = u:getPlayerName(),
              }
              local okf, fuel = pcall(function() return u:getFuel() end)
              if okf and fuel and cat <= 1 then du.carburante = fuel end
              local okv, vel = pcall(function() return u:getVelocity() end)
              if okv and vel then du.velocita = math.sqrt(vel.x ^ 2 + vel.y ^ 2 + vel.z ^ 2) end
              gg.unita[#gg.unita + 1] = du
            end
          end
          stato.gruppi[#stato.gruppi + 1] = gg
        end
      end
    end
    for _, s in pairs(coalition.getStaticObjects(coal) or {}) do
      if s and s:isExist() then
        stato.statici[#stato.statici + 1] = {
          nome = s:getName(), tipo = s:getTypeName(), coalizione = NOMI_COAL[coal],
          vita = s:getLife(), pos = posizione(s),
        }
      end
    end
  end
  -- stato delle basi aeree (proprietario)
  stato.basi = {}
  for _, ab in pairs(world.getAirbases() or {}) do
    local ok, desc = pcall(function() return ab:getDesc() end)
    if ok and desc and desc.category == Airbase.Category.AIRDROME then
      stato.basi[#stato.basi + 1] = { nome = ab:getName(), coalizione = NOMI_COAL[ab:getCoalition()] }
    end
  end
  return stato
end

function LEVANTE.salva(motivo)
  if not LEVANTE.salvataggioAttivo then return false end
  local ok, err = pcall(function()
    local stato = LEVANTE.fotografia()
    stato.motivo = motivo
    LEVANTE.scriviFile("stato_" .. LEVANTE.missione .. ".lua", "stato", stato)
    LEVANTE.scriviFile("registro_" .. LEVANTE.missione .. ".lua", "registro", {
      missione = LEVANTE.missione, motivo = motivo, ora = orologio(), eventi = LEVANTE.registro,
    })
  end)
  if ok then
    log("stato salvato (" .. tostring(motivo) .. ")")
  else
    log("ERRORE salvataggio: " .. tostring(err))
  end
  return ok
end

------------------------------------------------------------------------
-- Avvio
------------------------------------------------------------------------
local menu = missionCommands.addSubMenu("Levante 1989")
missionCommands.addCommand("Salva lo stato adesso", menu, function()
  if LEVANTE.salva("manuale") then
    avviso("Stato salvato in " .. LEVANTE.cartella, 10)
  else
    avviso("Salvataggio NON riuscito: controlla MissionScripting.lua", 15)
  end
end)
LEVANTE.menu = menu

if LEVANTE.salvataggioAttivo then
  timer.scheduleFunction(function(_, t)
    LEVANTE.salva("automatico")
    return t + LEVANTE.autosave
  end, nil, timer.getTime() + LEVANTE.autosave)
  timer.scheduleFunction(function()
    LEVANTE.salva("avvio")
    avviso("Levante 1989: salvataggio dello stato ATTIVO.\nCartella: " .. LEVANTE.cartella, 15)
  end, nil, timer.getTime() + 5)
else
  timer.scheduleFunction(function()
    avviso("ATTENZIONE - Levante 1989: salvataggio dello stato DISATTIVATO.\n" ..
      "MissionScripting.lua non e' stato modificato (io/lfs bloccati).\n" ..
      "Vedi il README della campagna.", 60)
  end, nil, timer.getTime() + 5)
end

log("nucleo " .. LEVANTE.versione .. " caricato, missione " .. LEVANTE.missione ..
  ", salvataggio " .. (LEVANTE.salvataggioAttivo and "attivo" or "DISATTIVATO"))
