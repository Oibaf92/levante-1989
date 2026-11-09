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

local ax, az, ah, spostA = cercaPunto(P.x, P.y, 350, 400, 8000)
if not ax then
  log("nessun punto adatto trovato: uso la posizione prevista")
  ax, az, ah, spostA = P.x, P.y, land.getHeight({ x = P.x, y = P.y }), 0
end

local bx, bz, bh
for _, rotta in ipairs({ 90, 270, 0, 180, 45, 135, 225, 315 }) do
  local r = math.rad(rotta)
  local x, z = ax + 900 * math.cos(r), az + 900 * math.sin(r)
  local ok, h = terrenoAdatto(x, z, 200)
  if ok then bx, bz, bh = x, z, h; break end
end
if not bx then
  bx, bz = ax + 900, az
  bh = land.getHeight({ x = bx, y = bz })
end
log(string.format("bersaglio A a %.0f m dal punto previsto; B a 900 m da A", spostA))

------------------------------------------------------------------------
-- Creazione dei bersagli (oggetti statici)
------------------------------------------------------------------------
local contatore = 0
local function statico(tipo, categoria, x, z, rotta)
  contatore = contatore + 1
  coalition.addStaticObject(PAESE, {
    type = tipo, category = categoria,
    name = string.format("Poligono-%02d", contatore),
    x = x, y = z, heading = math.rad(rotta or 0), dead = false,
  })
end

-- Bersaglio A (bombe Mk-82): tre carri in disuso al centro, quattro camion come riferimento
statico("T-55", "Armor", ax, az, 40)
statico("T-55", "Armor", ax + 12, az + 8, 120)
statico("T-55", "Armor", ax - 10, az + 11, 300)
for i = 0, 3 do
  local a = math.rad(i * 90)
  statico("Ural-375", "Unarmed", ax + 80 * math.cos(a), az + 80 * math.sin(a), i * 90)
end

-- Bersaglio B (BDU-33 da esercitazione): un blindato al centro, cerchio di fuoristrada a 50 m
statico("BTR-80", "Armor", bx, bz, 0)
for i = 0, 5 do
  local a = math.rad(i * 60)
  statico("UAZ-469", "Unarmed", bx + 50 * math.cos(a), bz + 50 * math.sin(a), i * 60 + 90)
end

------------------------------------------------------------------------
-- Poligono MOOSE
------------------------------------------------------------------------
local coordA = COORDINATE:New(ax, ah, az)
local coordB = COORDINATE:New(bx, bh, bz)

local poligono = RANGE:New("Poligono Ceyhan")
poligono:AddBombingTargetCoordinate(coordA, "Bersaglio A", 25)
poligono:AddBombingTargetCoordinate(coordB, "Bersaglio B", 15)
poligono:SetScoreBombDistance(1500)
poligono:SetRangeRadius(6)
poligono:SetMessageTimeDuration(20)
poligono:Start()

LEVANTE.extra = LEVANTE.extra or {}
LEVANTE.extra.poligono = {
  bersaglio_A = { x = ax, y = az, alt = ah, spostamento = spostA },
  bersaglio_B = { x = bx, y = bz, alt = bh },
  impatti = {},
}

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
-- Fumogeni, segni F10, informazioni
------------------------------------------------------------------------
local function fumogeni()
  trigger.action.smoke({ x = ax + 120, y = ah, z = az + 120 }, trigger.smokeColor.Orange)
  trigger.action.smoke({ x = bx + 80, y = bh, z = bz + 80 }, trigger.smokeColor.Blue)
end
fumogeni()
timer.scheduleFunction(function(_, t) fumogeni(); return t + 300 end, nil, timer.getTime() + 300)

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

local llA = testoLL(ax, ah, az)
local llB = testoLL(bx, bh, bz)
local quotaA = math.floor(ah * 3.28084 + 0.5)
local quotaB = math.floor(bh * 3.28084 + 0.5)

trigger.action.markToAll(9001, "Bersaglio A (Mk-82) - fumo arancione\n" .. llA .. "\nQuota " .. quotaA .. " ft", { x = ax, y = ah, z = az }, true)
trigger.action.markToAll(9002, "Bersaglio B (BDU-33) - fumo blu\n" .. llB .. "\nQuota " .. quotaB .. " ft", { x = bx, y = bh, z = bz }, true)

local function info()
  local testo = "POLIGONO DI CEYHAN\n\n" ..
    "Bersaglio A (Mk-82) - fumo ARANCIONE\n  " .. llA .. "   quota " .. quotaA .. " ft\n\n" ..
    "Bersaglio B (BDU-33) - fumo BLU\n  " .. llB .. "   quota " .. quotaB .. " ft\n\n" ..
    "I bersagli sono anche segnati sulla mappa F10."
  if spostA > 300 then
    testo = testo .. string.format("\n\nNOTA: il bersaglio A e' a %.1f km dal waypoint ST del piano di volo.", spostA / 1000)
  end
  trigger.action.outText(testo, 30)
end
missionCommands.addCommand("Informazioni poligono", LEVANTE.menu, info)

timer.scheduleFunction(function()
  trigger.action.outText("Poligono di Ceyhan attivo. Menu F10 > Levante 1989 > Informazioni poligono.", 15)
end, nil, timer.getTime() + 20)

log("poligono pronto")
