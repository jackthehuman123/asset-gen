--[[
	THROWAWAY SPIKE, run 6: one detailed piece of furniture.

	ONE generation at the maximum triangle budget, shown as two copies side by side:
	  1. GENERATED - Roblox's own texture
	  2. MATERIAL  - texture removed, a Roblox material applied
	Both at real-world size next to a 5.5-stud character marker.

	Put this Script in ServerScriptService and press Play.
	To keep results: while playing, copy Workspace > GenTestResults,
	stop, then paste into Workspace.
]]

local GenerationService = game:GetService("GenerationService")

------------------------------------------------------------------------
-- CONFIG
------------------------------------------------------------------------

local PROMPT = "a modern wooden cabinet with two doors and three drawers, slim metal handles, "
	.. "thin tapered legs, clean straight lines, sharp edges, flat panels, visible panel seams, "
	.. "highly detailed"

local MAX_TRIANGLES = 20000
local TARGET_HEIGHT = 3 -- studs (about waist height next to a 5.5-stud character)

local MATERIAL = Enum.Material.Wood
local COLOR = Color3.fromRGB(150, 110, 72)

------------------------------------------------------------------------
-- RUN
------------------------------------------------------------------------

local results = Instance.new("Folder")
results.Name = "GenTestResults"
results.Parent = workspace

local function addLabel(pos, text)
	local a = Instance.new("Part")
	a.Name = "Label"
	a.Anchored = true
	a.CanCollide = false
	a.Transparency = 1
	a.Size = Vector3.one
	a.Position = pos
	a.Parent = results
	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromOffset(200, 36)
	gui.AlwaysOnTop = true
	gui.Parent = a
	local tl = Instance.new("TextLabel")
	tl.Size = UDim2.fromScale(1, 1)
	tl.BackgroundTransparency = 0.4
	tl.BackgroundColor3 = Color3.new(0, 0, 0)
	tl.TextColor3 = Color3.new(1, 1, 1)
	tl.TextScaled = true
	tl.Text = text
	tl.Parent = gui
end

print("[GenTest] generating cabinet ...")
local t0 = os.clock()
local ok, model = pcall(function()
	return GenerationService:GenerateModelAsync({
		TextPrompt = PROMPT,
		MaxTriangles = MAX_TRIANGLES,
		GenerateTextures = true,
	}, { PredefinedSchema = "Body1" })
end)
local secs = os.clock() - t0

if not ok or not model then
	warn(("[GenTest] FAILED after %.1fs: %s"):format(secs, tostring(model)))
	return
end

model.Parent = results
local _, raw = model:GetBoundingBox()
model:ScaleTo(model:GetScale() * (TARGET_HEIGHT / raw.Y))

local meshes, hasTexture = 0, false
for _, d in model:GetDescendants() do
	if d:IsA("BasePart") then
		d.Anchored = true
	end
	if d:IsA("MeshPart") then
		meshes += 1
		if d:FindFirstChildWhichIsA("SurfaceAppearance") or (d.TextureID ~= "") then
			hasTexture = true
		end
	end
end

local copies = { { model, "1. GENERATED" }, { model:Clone(), "2. MATERIAL" } }
for i, c in copies do
	local m, label = c[1], c[2]
	m.Name = label
	m.Parent = results
	if i == 2 then
		for _, d in m:GetDescendants() do
			if d:IsA("SurfaceAppearance") then
				d:Destroy()
			elseif d:IsA("BasePart") then
				pcall(function() d.TextureID = "" end)
				d.Material = MATERIAL
				d.Color = COLOR
			end
		end
	end
	local _, s = m:GetBoundingBox()
	local pos = Vector3.new((i - 1) * 10, s.Y / 2, 0)
	m:PivotTo(CFrame.new(pos))
	addLabel(pos + Vector3.new(0, s.Y / 2 + 2, 0), label)
end

local marker = Instance.new("Part")
marker.Name = "PlayerHeightMarker"
marker.Anchored = true
marker.Size = Vector3.new(2, 5.5, 1)
marker.Position = Vector3.new(-5, 2.75, 0)
marker.Color = Color3.fromRGB(160, 160, 160)
marker.Material = Enum.Material.SmoothPlastic
marker.Parent = results

local _, final = model:GetBoundingBox()
print("\n========== GENERATION TEST (run 6: one cabinet) ==========")
print(("generated in %.1fs, %d mesh(es), texture=%s"):format(secs, meshes, tostring(hasTexture)))
print(("raw size %s -> scaled %s"):format(tostring(raw), tostring(final)))
print("===========================================================")
