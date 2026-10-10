# -*- coding: utf-8 -*-
"""Catalogue of vanilla Outer Wilds scene objects that are safe to copy with New Horizons `details`.

Every path comes from the community prop list, the New Horizons documentation/source or from published
NH addons that already copy it. Shared by all build scripts and the validator.
"""

# --------------------------------------------------------------------------------------------
# Verified scene paths of vanilla props (community prop list + NH docs/examples).
# --------------------------------------------------------------------------------------------
P = {
    "vase_thick": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_VaseThick",
    "vase_thin": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_VaseThin",
    "vase_broken": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_VaseThick_Broken",
    "treepot": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_Treepot",
    "potted_tree": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_NomaiTree_Var_1",
    "potted_tree2": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_NomaiTree_Var_2",
    "dry_tree": "Shuttle_Body/Prefab_NOM_Shuttle/Sector_NomaiShuttleInterior/Props_NomaiShuttleInterior/Prefab_NOM_NomaiTree_VarDRY_3",
    "bench": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_SimpleChair_NoSkeleton (1)",
    "bench_skeleton": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_NorthPoleSurface/Props_NorthPoleSurface/OtherComponentsGroup/LowBuilding/Prefab_NOM_SimpleChair",
    "skeleton": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_NorthPoleSurface/Props_NorthPoleSurface/OtherComponentsGroup/LowBuilding/Prefab_NOM_Skeleton_Large_Pile_A",
    "shelf": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_Shelf (2)/Strucutre_NOM_Shelf",
    "table": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Props_NOM_Table",
    "staff": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_Staff",
    "bowl": "BrittleHollow_Body/Sector_BH/Sector_GravityCannon/Props_GravityCannon/OtherComponentsGroup/Prefab_NOM_SmallBowl",
    "toys": "BrittleHollow_Body/Sector_BH/Sector_GravityCannon/Props_GravityCannon/OtherComponentsGroup/Prefab_NOM_Toys",
    "box": "Comet_Body/Sector_CO/Sector_CometInterior/Props_CometInterior/Prefab_NOM_Box",
    "box_broken": "Comet_Body/Sector_CO/Sector_CometInterior/Props_CometInterior/Prefab_NOM_BoxBroken",
    "container": "Comet_Body/Sector_CO/Sector_CometInterior/Props_CometInterior/Prefab_NOM_Container",
    "torch": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthSurface/Sector_SouthPole/Lighting_SouthPole/Prefab_NOM_Torch",
    "lamp_flare": "BrittleHollow_Body/Sector_BH/Sector_EscapePodCrashSite/Sector_NorthFragment/Interactables_NorthFragment/VisibleFrom_EscapePodCrashSite/Prefab_NOM_Lamp_EscapePodFlare",
    "doorway": "BrittleHollow_Body/Sector_BH/Sector_GravityCannon/Lighting_GravityCannon/Prefab_NOM_Doorway",
    "doorway_fancy": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_City/Lighting_City/Lights_ForumDistrict/TractorBeamFacadeDoors/Prefab_NOM_Doorway_Fancy",
    "eye_symbol": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_City/Lighting_City/Lights_EyeDistrict/Props_NOM_EyeSymbolCopper",
    "gateway": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_City/Interactables_City/CityDoors/Prefab_NOM_Gateway",
    "probe_window": "StatueIsland_Body/Sector_StatueIsland/Interactables_StatueIsland/CenterRuin/Structure_NOM_ProbeFloor_StatueIsland",
    "tractor_large": "StatueIsland_Body/Sector_StatueIsland/Interactables_StatueIsland/ControlledByProxy_StatueIsland/Props_NOM_DockingTractorBeam (1)",
    "gravity_cannon": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_GravityCannon/Geometry_GravityCannon/ControlledByProxy_Arch/Structure_NOM_GravityCannon_HT",
    "crystal_cracked": "BrittleHollow_Body/Sector_BH/Sector Quantum Pole Path/Fragment QuantumPolePath 2/Interactables_QPP2/Prefab_NOM_GravityCrystal_Cracked",
    "bridge": "BrittleHollow_Body/Sector_BH/Sector_OldSettlement/OldSettlement_Interactables/Structure_NOM_BH_OldSettleBridge_Placements/Structure_NOM_BH_OldSettleBridge16",
    "platform_broken": "BrittleHollow_Body/Sector_BH/Sector_EscapePodCrashSite/Sector_CrashFragment/Interactables_CrashFragment/Platforms/Prefab_NOM_BrokenPlatform",
    "symbols3": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_Entrance/Interactables_HangingCity_Entrance/ModuleSymbol (6)",
    "pottery": "StatueIsland_Body/Sector_StatueIsland/DetailPatches_StatueIsland/Foliage_StatueIsland_TopBits/Clutter_NOM_Pottery (%d)",
    "transponder": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_EscapePod/Interactables_EscapePod/EscapePod_VisibleFrom_Far/DistressBeaconTransmitter/Props_NOM_Transponder",
    "light_beam": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_EscapePod/Interactables_EscapePod/EscapePod_VisibleFrom_Far/DistressBeaconTransmitter/LightBeam",
    # base game only: no Echoes of the Eye (DreamWorld/RingWorld) props, so the mod works without the DLC
    "gd_tree": "QuantumMoon_Body/Sector_QuantumMoon/State_GD/Interactables_GDState/GDState_Quantum_Objects/Quantum_TreeClump_1/Rock_Tree",
    "th_sapling": "QuantumMoon_Body/Sector_QuantumMoon/State_TH/Interactables_THState/Crater_3/Crater_3_Sapling/QSapling/Tree_TH_Sapling",
    "alpine_clump": "QuantumMoon_Body/Sector_QuantumMoon/State_TH/Interactables_THState/Crater_Surface/Surface_AlpineClump_S/Surface_AlpineClump_S/BatchedGroup",
    "purple_rock": "QuantumMoon_Body/Sector_QuantumMoon/State_EYE/Interactables_EYEState/EYEState_QuantumObjects/EYE_Q_Arch_B/EYE_Q_ArchB/Rocks_EYE_Arch_B",
    "ice_lump": "BrittleHollow_Body/Sector_BH/Sector Great Southern Triangle/Fragment 71_GreatSouthernTriangle/Core_Fragment_71_GreatSouthernTriangle/Props_Core_Fragment_71_GreatSouthernTriangle/Ice_BH_Lump_B",
    "bh_tree": "BrittleHollow_Body/Sector_BH/Sector_GravityCannon/Props_GravityCannon/OtherComponentsGroup/VisibleFrom_BH/Prefab_Tree_BH_Bristle",
    "cactus": "QuantumMoon_Body/Sector_QuantumMoon/State_HT/Interactables_HTState/Interactables_CTState/CTState_Q_Objects/CTState_QCactus/Q_Cactus/Prefab_HGT_Cactus_Single_A",
    # ---- buildings and large structures (paths used by published NH addons) ----
    "shrine": "QuantumMoon_Body/Sector_QuantumMoon/QuantumShrine/Structure_NOM_QuantumShrine",
    "arch": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthSurface/Sector_WarpReceiver/Geometry_WarpReceiver/OtherComponentsGroup/Prefab_NOM_Arch_B",
    "stairs_l": "BrittleHollow_Body/Sector_BH/Sector Cannon Path/Fragment CannonPath_3/Core_CannonPath_3/Geometry_Core_CannonPath_3/Architecture_CannonPath_3/OtherComponentsGroup/Prefab_NOM_Stairs_Solid_L",
    "stairs_r": "BrittleHollow_Body/Sector_BH/Sector Cannon Path/Fragment CannonPath_3/Core_CannonPath_3/Geometry_Core_CannonPath_3/Architecture_CannonPath_3/OtherComponentsGroup/Prefab_NOM_Stairs_Solid_R",
    "stargazing": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthSurface/Sector_SouthPole/Interactables_SouthPole/SouthPole_VisibleFromFar/Structure_NOM_StargazingPlatform/StargazingPlatform",
    "cannon_platform": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_GravityCannon/Geometry_GravityCannon/ControlledByProxy_Arch/Structure_NOM_GravityCannon_HT/Structure_NOM_GravityCannon/Structure_NOM_GravityCannon_LaunchingPlatform",
    "escape_pod": "BrittleHollow_Body/Sector_BH/Sector_EscapePodCrashSite/Sector_CrashFragment/EscapePod_Socket",
    "escape_pod_geo": "DB_EscapePodDimension_Body/Sector_EscapePodDimension/Sector_EscapePodBody/Geometry_EscapePodBody",
    "dead_suit": "Comet_Body/Sector_CO/Sector_CometInterior/Props_CometInterior/Prefab_NOM_Dead_Suit (1)",
    "skeleton_child": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_FossilCave/Geometry_FossilCave/OtherComponentsGroup/Child Skeletons/Prefab_NOM_Skeleton_Child_Pile_A",
    "opc_module": "OrbitalProbeCannon_Body/Sector_OrbitalProbeCannon/Sector_Module_Broken",
    "opc_module_intact": "OrbitalProbeCannon_Body/Sector_OrbitalProbeCannon/Sector_Module_Intact",
    "nomai_probe": "NomaiProbe_Body/Structure_NOM_Probe_Renderer",
    "sunstation": "SunStation_Body/Sector_SunStation/Geometry_SunStation",
    "statue_head": "SunStation_Body/Sector_SunStation/Sector_ControlModule/Props/OtherComponentsGroup/StatueHead/Prefab_NOM_StatueHead",
    "whs_geo": "WhiteholeStation_Body/Sector_WhiteholeStation/Geometry_WhiteholeStation",
    "vessel_lamp": "DB_VesselDimension_Body/Sector_VesselDimension/Sector_VesselBridge/Interactibles_VesselBridge/UNSORTED/Wall Lamps/Prefab_NOM_Lamp_Glow_Vessel_Wall",
    "warpcore_broken": "CaveTwin_Body/Sector_CaveTwin/Sector_NorthHemisphere/Sector_NorthSurface/Sector_TimeLoopExperiment/WarpCoreWallSockets/WarpCoreSocket/Props_NOM_WarpCoreBroken (1)/Props_NOM_WarpCore_Simple",
    "bramble_seed": "TimberHearth_Body/Sector_TH/Sector_ImpactCrater/Interactables_ImpactCrater/ControlledByProxy_Structures/Terrain_DB_BrambleSphere_Seed_V2",
    # the real Dark Bramble vines (quantum state of the Quantum Moon), variants 1-5
    "db_vine": "QuantumMoon_Body/Sector_QuantumMoon/State_DB/Interactables_DBState/DBState_QuantumObjects/DB_Q_Vine{n}/DB_Bramble_Vine{n}/State_1/Terrain_TH_Bramble_Vine{n}",
    "angler": "DB_HubDimension_Body/Sector_HubDimension/Interactables_HubDimension/Anglerfish_Body",
    "wall_lamp": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_City/Lighting_City/Lights_FossilDistrict/Prefab_NOM_Lamp_Glow_Diamond_Wall",
    "gravity_crystal": "BrittleHollow_Body/Sector_BH/Sector Quantum Pole Path/Fragment QuantumPolePath 2/Interactables_QPP2/Prefab_NOM_GravityCrystal",
    # ---- Interstellare Sonden Aussendungseinheit ----
    # whole Orbital Probe Cannon sector (hub, barrel, control and launch module) as it is before it fires
    "opc_sector": "OrbitalProbeCannon_Body/Sector_OrbitalProbeCannon",
    "grav_cannon_bh": "BrittleHollow_Body/Sector_BH/Sector_GravityCannon/Geometry_GravityCannon/ControlledByProxy_OPC/Structure_NOM_GravityCannon_BH",
    "warp_particles": "TowerTwin_Body/Sector_TowerTwin/Sector_TimeLoopInterior/Interactables_TimeLoopInterior/WarpCoreSocket/Prefab_NOM_WarpCoreVessel/Effects_NOM_AdvancedWarpCore/Effects_NOM_WarpParticlesWhite",
    # the advanced warp core of the Vessel (in the Ash Twin Project) and the Vessel's coordinate interface
    "warpcore_vessel": "TowerTwin_Body/Sector_TowerTwin/Sector_TimeLoopInterior/Interactables_TimeLoopInterior/WarpCoreSocket/Prefab_NOM_WarpCoreVessel",
    "vessel_interface": "DB_VesselDimension_Body/Sector_VesselDimension/Sector_VesselBridge/Interactibles_VesselBridge/WarpController/CoordinateInterface",
    # the rings of the Construction Yard on Giant's Deep, where the Orbital Probe Cannon was built
    "construction_rings": "ConstructionYardIsland_Body/Sector_ConstructionYard/Geometry_ConstructionYard/OtherComponentsGroup/ControlledByProxy_ConstructionYard/ConstructionRings",
}

# Vertical correction per prop (metres along the local up axis). Vanilla props do not all have their pivot
# at the base, so small objects are sunk a few centimetres and large structures a bit more: a prop that is
# slightly embedded looks right, a floating one does not. Tune single values here after testing in game.
GROUND = {
    "default": -0.05,
    "doorway": -0.15, "doorway_fancy": -0.15, "gateway": -0.2, "arch": -0.2,
    "shrine": -0.35, "stargazing": -0.2, "cannon_platform": -0.3, "gravity_cannon": -0.5,
    "escape_pod": -0.9, "escape_pod_geo": -0.6, "crystal_cracked": -0.3, "probe_window": -0.1,
    "transponder": -0.2, "bramble_seed": -1.5, "purple_rock": -0.5, "ice_lump": -0.3,
    "stairs_l": -0.1, "stairs_r": -0.1,
}

SCENE_PROPS = set(P.values()) | {P["pottery"] % i for i in range(1, 15)} | {P["db_vine"].format(n=n) for n in range(1, 6)}
