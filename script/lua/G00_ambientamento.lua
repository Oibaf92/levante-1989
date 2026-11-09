--[[
  LEVANTE 1989 - G00 "Ambientamento"
  Poligono di tiro NATO di Ceyhan (Turchia meridionale).

  * cerca un punto adatto vicino alla posizione prevista (terreno solido,
    pianeggiante, senza edifici) e vi crea i due bersagli
  * crea il poligono MOOSE RANGE: distanza e radiale di ogni impatto
  * fumogeni sui bersagli ogni 5 minuti, segni sulla mappa F10
  * i risultati finiscono nello stato salvato dal nucleo (LEVANTE.extra)

  Richiede: Moose.lua e levante_core.lua caricati prima.
  Parametri in LEVANTE.poligono = { x = ..., y = ... } (coordinate mappa DCS).
]]

local P = LEVANTE.poligono or { x = 207254, y = -24700 }
local PAESE = country.id.USA

local function log(msg) env.info("[LEVANTE G00] " .. msg) end

------------------------------------------------------------------------
-- Ricerca di un punto adatto
------------------------------------------------------------------------
local function superficieOk(x, z)
  local s = land.getSurfaceType({ x = x, y = z })
  return s == land.SurfaceType.LAND or s == land.SurfaceType.ROAD
end

local function contaEdifici(x, h, z, raggio)
  local n = 0
  local vol = { id = world.VolumeType.SPHERE, params = { point = { x = x, y = h, z = z }, radius = raggio } }
  world.searchObjects(Object.Category.SCENERY, vol, function() n = n + 1; return true end)
  return n
end

local function terrenoAdatto(x, z, raggio)
  if land.getSurfaceType({ x = x, y = z }) ~= land.SurfaceType.LAND then return false end
  local h0 = land.getHeight({ x = x, y = z })
  local hmin, hmax = h0, h0
  for i = 0, 11 do
    local a = i * math.pi / 6
    for _, r in ipairs({ raggio * 0.5, raggio }) do
      local px, pz = x + r * math.cos(a), z + r * math.sin(a)
      if not superficieOk(px, pz) then return false end
      local h = land.getHeight({ x = px, y = pz })
      if h < hmin then hmin = h end
      if h > hmax then hmax = h end
    end
  end
  if hmax - hmin > 15 then return false end
  if contaEdifici(x, h0, z, raggio) > 0 then return false end
  return true, h0
end

local function cercaPunto(x0, z0, raggio, passo, maxDist)
  for r = 0, maxDist, passo do
    local n = (r == 0) and 1 or math.max(8, math.floor(2 * math.pi * r / passo))
    for i = 0, n - 1 do
      local a = 2 * math.pi * i / n
      local x, z = x0 + r * math.cos(a), z0 + r * math.sin(a)
      local ok, h = terrenoAdatto(x, z, raggio)
      if ok then return x, z, h, r end
    end
  end
  return nil
end


------------------------------------------------------------------------
-- Posizione del poligono
--   1. se esiste una posizione scelta dal giocatore in un volo precedente
--      (file poligono_G00.lua), usa quella
--   2. altrimenti cerca un punto adatto vicino alla posizione prevista
-- Le foreste NON sono rilevabili dagli script: il giocatore puo' spostare
-- il poligono con un segno F10 contenente la parola "poligono".
------------------------------------------------------------------------
local FILE_POSIZIONE = "poligono_G00_v2.lua"   -- v2: nuova posizione prevista (campo aperto)

local function posizioneSalvata()
  if not LEVANTE.salvataggioAttivo then return nil end
  local f = io.open(LEVANTE.cartella .. FILE_POSIZIONE, "r")
  if not f then return nil end
  local testo = f:read("*a")
  f:close()
  local fn = loadstring(testo)
  if not fn then return nil end
  local env = {}
  setfenv(fn, env)
  if not pcall(fn) or type(env.poligono) ~= "table" then return nil end
  return env.poligono.x, env.poligono.y
end

local function trovaB(ax, az)
  for _, rotta in ipairs({ 90, 270, 0, 180, 45, 135, 225, 315 }) do
    local r = math.rad(rotta)
    local x, z = ax + 900 * math.cos(r), az + 900 * math.sin(r)
    local ok, h = terrenoAdatto(x, z, 200)
    if ok then return x, z, h end
  end
  local x, z = ax + 900, az
  return x, z, land.getHeight({ x = x, y = z })
end

local ax, az, ah, bx, bz, bh
local spostA = 0
local origine = "prevista"

do
  local sx, sz = posizioneSalvata()
  if sx then
    ax, az = sx, sz
    ah = land.getHeight({ x = ax, y = az })
    origine = "scelta dal giocatore"
  else
    ax, az, ah, spostA = cercaPunto(P.x, P.y, 350, 400, 8000)
    if not ax then
      ax, az, ah, spostA = P.x, P.y, land.getHeight({ x = P.x, y = P.y }), 0
    end
  end
  bx, bz, bh = trovaB(ax, az)
end

------------------------------------------------------------------------
-- Creazione e rimozione dei bersagli (oggetti statici)
------------------------------------------------------------------------
local creati = {}
local generazione = 0

local function statico(tipo, categoria, x, z, rotta)
  local nome = string.format("Poligono-%d-%02d", generazione, #creati + 1)
  coalition.addStaticObject(PAESE, {
    type = tipo, category = categoria, name = nome,
    x = x, y = z, heading = math.rad(rotta or 0), dead = false,
  })
  creati[#creati + 1] = nome
end

local function rimuoviBersagli()
  for _, nome in ipairs(creati) do
    local s = StaticObject.getByName(nome)
    if s then pcall(function() s:destroy() end) end
  end
  creati = {}
end

local function creaBersagli()
  generazione = generazione + 1
  -- A (Mk-82): tre carri in disuso al centro, quattro camion di riferimento a 80 m
  statico("T-55", "Armor", ax, az, 40)
  statico("T-55", "Armor", ax + 12, az + 8, 120)
  statico("T-55", "Armor", ax - 10, az + 11, 300)
  for i = 0, 3 do
    local a = math.rad(i * 90)
    statico("Ural-375", "Unarmed", ax + 80 * math.cos(a), az + 80 * math.sin(a), i * 90)
  end
  -- B (BDU-33): un blindato al centro, cerchio di fuoristrada a 50 m
  statico("BTR-80", "Armor", bx, bz, 0)
  for i = 0, 5 do
    local a = math.rad(i * 60)
    statico("UAZ-469", "Unarmed", bx + 50 * math.cos(a), bz + 50 * math.sin(a), i * 60 + 90)
  end
end

------------------------------------------------------------------------
-- Testi, segni F10
------------------------------------------------------------------------
local function testoLL(x, h, z)
  local lat, lon = coord.LOtoLL({ x = x, y = h, z = z })
  local function f(v, p, n)
    local e = v >= 0 and p or n
    v = math.abs(v)
    local g = math.floor(v)
    return string.format("%s %02d°%06.3f'", e, g, (v - g) * 60)
  end
  return f(lat, "N", "S") .. "  " .. f(lon, "E", "W")
end

local function ft(m) return math.floor(m * 3.28084 + 0.5) end

local function aggiornaSegni()
  trigger.action.removeMark(9001)
  trigger.action.removeMark(9002)
  trigger.action.markToAll(9001, "Bersaglio A (Mk-82) - fumo arancione\n" .. testoLL(ax, ah, az) ..
    "\nQuota " .. ft(ah) .. " ft", { x = ax, y = ah, z = az }, true)
  trigger.action.markToAll(9002, "Bersaglio B (BDU-33) - fumo blu\n" .. testoLL(bx, bh, bz) ..
    "\nQuota " .. ft(bh) .. " ft", { x = bx, y = bh, z = bz }, true)
end

local function info()
  local testo = "POLIGONO DI CEYHAN (posizione " .. origine .. ")\n\n" ..
    "Bersaglio A (Mk-82) - fumo ARANCIONE\n  " .. testoLL(ax, ah, az) .. "   quota " .. ft(ah) .. " ft\n\n" ..
    "Bersaglio B (BDU-33) - fumo BLU\n  " .. testoLL(bx, bh, bz) .. "   quota " .. ft(bh) .. " ft\n\n" ..
    "I bersagli sono anche segnati sulla mappa F10.\n" ..
    "Per spostare il poligono: sulla mappa F10 aggiungi un segno con scritto POLIGONO."
  if origine == "prevista" and spostA > 300 then
    testo = testo .. string.format("\n\nNOTA: il bersaglio A e' a %.1f km dal waypoint ST del piano di volo.", spostA / 1000)
  end
  trigger.action.outText(testo, 30)
end

------------------------------------------------------------------------
-- Poligono MOOSE
------------------------------------------------------------------------
creaBersagli()

local poligono = RANGE:New("Poligono Ceyhan")
poligono:AddBombingTargetCoordinate(COORDINATE:New(ax, ah, az), "Bersaglio A", 25)
poligono:AddBombingTargetCoordinate(COORDINATE:New(bx, bh, bz), "Bersaglio B", 15)
poligono:SetScoreBombDistance(1500)
poligono:SetRangeRadius(6)
poligono:SetMessageTimeDuration(20)
poligono:Start()

LEVANTE.extra = LEVANTE.extra or {}
LEVANTE.extra.poligono = { impatti = {} }

local function registraPosizione()
  LEVANTE.extra.poligono.origine = origine
  LEVANTE.extra.poligono.bersaglio_A = { x = ax, y = az, alt = ah, spostamento = spostA }
  LEVANTE.extra.poligono.bersaglio_B = { x = bx, y = bz, alt = bh }
end
registraPosizione()
aggiornaSegni()

function poligono:OnAfterImpact(From, Event, To, result, player)
  local r = {
    giocatore = result.player, bersaglio = result.name, arma = result.weapon,
    distanza_m = result.distance, radiale = result.radial, qualita = result.quality,
    rotta_attacco = result.attackHdg, quota_attacco_ft = result.attackAlt,
    velocita_attacco_kt = result.attackVel, ora = result.clock,
  }
  local imp = LEVANTE.extra.poligono.impatti
  imp[#imp + 1] = r
  LEVANTE.annota("impatto_poligono", r)
end

------------------------------------------------------------------------
-- Spostamento del poligono con un segno F10 ("poligono")
------------------------------------------------------------------------
local function spostaPoligono(pos)
  local x, z = pos.x, pos.z
  local s = land.getSurfaceType({ x = x, y = z })
  if s ~= land.SurfaceType.LAND and s ~= land.SurfaceType.ROAD then
    trigger.action.outText("Poligono NON spostato: il punto scelto non e' terraferma.", 15)
    return
  end
  rimuoviBersagli()
  ax, az = x, z
  ah = land.getHeight({ x = ax, y = az })
  bx, bz, bh = trovaB(ax, az)
  origine = "scelta dal giocatore"
  spostA = 0
  creaBersagli()

  -- aggiorna i bersagli e la zona del poligono MOOSE
  local cA, cB = COORDINATE:New(ax, ah, az), COORDINATE:New(bx, bh, bz)
  for _, t in ipairs(poligono.bombingTargets) do
    if t.name == "Bersaglio A" then t.coordinate = cA else t.coordinate = cB end
  end
  poligono.location = cA
  poligono.rangezone = ZONE_RADIUS:New(poligono.rangename, { x = ax, y = az }, poligono.rangeradius)

  registraPosizione()
  aggiornaSegni()

  -- ricorda la posizione per i voli successivi
  if LEVANTE.salvataggioAttivo then
    LEVANTE.scriviFile(FILE_POSIZIONE, "poligono", { x = ax, y = az })
    LEVANTE.salva("poligono_spostato")
  end
  LEVANTE.annota("poligono_spostato", { x = ax, y = az })
  trigger.action.outText("Poligono spostato. La nuova posizione verra' usata anche nei prossimi voli.", 15)
  info()
end

local gestoreSegni = {}
function gestoreSegni:onEvent(e)
  if e.id ~= world.event.S_EVENT_MARK_ADDED and e.id ~= world.event.S_EVENT_MARK_CHANGE then return end
  if type(e.text) ~= "string" or not string.find(string.lower(e.text), "poligono", 1, true) then return end
  if e.idx == 9001 or e.idx == 9002 then return end
  local ok, err = pcall(spostaPoligono, e.pos)
  if not ok then env.info("[LEVANTE G00] errore spostamento poligono: " .. tostring(err)) end
  pcall(trigger.action.removeMark, e.idx)
end
world.addEventHandler(gestoreSegni)

------------------------------------------------------------------------
-- Fumogeni e menu
------------------------------------------------------------------------
local function fumogeni()
  trigger.action.smoke({ x = ax + 120, y = ah, z = az + 120 }, trigger.smokeColor.Orange)
  trigger.action.smoke({ x = bx + 80, y = bh, z = bz + 80 }, trigger.smokeColor.Blue)
end
fumogeni()
timer.scheduleFunction(function(_, t) fumogeni(); return t + 300 end, nil, timer.getTime() + 300)

missionCommands.addCommand("Informazioni poligono", LEVANTE.menu, info)
missionCommands.addCommand("Torna alla posizione prevista del poligono", LEVANTE.menu, function()
  if LEVANTE.salvataggioAttivo then
    local f = io.open(LEVANTE.cartella .. FILE_POSIZIONE, "w")
    if f then f:write("-- nessuna posizione scelta\n"); f:close() end
  end
  trigger.action.outText("Posizione scelta cancellata: dal prossimo avvio il poligono tornera' nella posizione prevista.", 15)
end)

------------------------------------------------------------------------
-- Gregari: resta solo quello dello slot scelto dal giocatore
------------------------------------------------------------------------
local SLOT = {
  { giocatore = "Dodge 1-1", gruppo = "Dodge 1 (avvio a freddo)", gregario = "Dodge 1-2" },
  { giocatore = "Dodge 2-1", gruppo = "Dodge 2 (motori accesi)", gregario = "Dodge 2-2" },
}

local function giocatorePresente(nome)
  local u = Unit.getByName(nome)
  return u ~= nil and u:isExist() and u:getPlayerName() ~= nil
end

local function sistemaGregari()
  local scelto = nil
  for _, s in ipairs(SLOT) do
    if giocatorePresente(s.giocatore) then scelto = s end
  end
  if not scelto then return false end
  for _, s in ipairs(SLOT) do
    if s ~= scelto then
      LEVANTE.ignora[s.gregario] = true
      local g = Group.getByName(s.gruppo)
      if g and g:isExist() then
        pcall(function() g:destroy() end)
        log("rimosso il gruppo non usato " .. s.gruppo)
      end
    end
  end
  return true
end

-- il giocatore puo' entrare nell'aereo qualche istante dopo l'avvio: riprova per 60 s
local tentativi = 0
timer.scheduleFunction(function(_, t)
  tentativi = tentativi + 1
  if sistemaGregari() or tentativi >= 60 then return nil end
  return t + 1
end, nil, timer.getTime() + 1)

timer.scheduleFunction(function()
  trigger.action.outText("Poligono di Ceyhan attivo (posizione " .. origine .. ").\n" ..
    "Menu F10 > Levante 1989 > Informazioni poligono.\n" ..
    "Per spostarlo: segno sulla mappa F10 con scritto POLIGONO.", 20)
end, nil, timer.getTime() + 20)

log(string.format("poligono pronto, posizione %s (spostamento %.0f m)", origine, spostA))
