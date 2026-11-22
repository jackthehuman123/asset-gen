--[[
	THROWAWAY SPIKE helper: run in Studio's COMMAND BAR after importing cabinet.fbx.

	- Finds the imported model (select it first, or it searches Workspace for "cabinet")
	- Applies Roblox materials by mesh name (Cabinet_Wood / Cabinet_Metal)
	- Rescales to 3 studs tall if the importer's units were off
	- Adds a 5.5-stud character marker beside it
]]

local Selection = game:GetService("Selection")
local TARGET_HEIGHT = 3

local model = Selection:Get()[1]
if not (model and model:IsA("Model")) then
	model = workspace:FindFirstChild("cabinet", true)
end
assert(model and model:IsA("Model"), "Select the imported cabinet model first")

local LOOKS = {
	Cabinet_Wood  = { Enum.Material.Wood,  Color3.fromRGB(120, 82, 52) },
	Cabinet_Metal = { Enum.Material.Metal, Color3.fromRGB(25, 25, 25) },
}

for _, d in model:GetDescendants() do
	if d:IsA("MeshPart") then
		d.Anchored = true
		for name, look in LOOKS do
			if string.find(d.Name, name, 1, true) then
				for _, c in d:GetChildren() do
					if c:IsA("SurfaceAppearance") then c:Destroy() end
				end
				pcall(function() d.TextureID = "" end)
				d.Material = look[1]
				d.Color = look[2]
			end
		end
	end
end

local _, size = model:GetBoundingBox()
print(("[cabinet] imported size %s"):format(tostring(size)))
if math.abs(size.Y - TARGET_HEIGHT) > 0.1 then
	model:ScaleTo(model:GetScale() * (TARGET_HEIGHT / size.Y))
	local _, s2 = model:GetBoundingBox()
	print(("[cabinet] rescaled to %s"):format(tostring(s2)))
end

local cf, s = model:GetBoundingBox()
local marker = Instance.new("Part")
marker.Name = "PlayerHeightMarker"
marker.Anchored = true
marker.Size = Vector3.new(2, 5.5, 1)
marker.CFrame = cf * CFrame.new(-s.X / 2 - 2, -s.Y / 2 + 2.75, 0)
marker.Color = Color3.fromRGB(160, 160, 160)
marker.Parent = workspace
