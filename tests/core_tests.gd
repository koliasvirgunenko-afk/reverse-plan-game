extends SceneTree
const Spatial = preload("res://core/spatial.gd")
var failed = 0
var passed = 0

func check(ok: bool, label: String):
	if ok:
		passed += 1
		print("PASS ", label)
	else:
		failed += 1
		push_error("FAIL " + label)

func _initialize():
	call_deferred("run")

func run():
	var source = Transform3D(Basis(Vector3.UP, 0.7), Vector3(3, 4, 8))
	var dest = Transform3D(Basis(Vector3.UP, -1.2), Vector3(-18, 1, 5))
	var original = Transform3D(Basis(Vector3.RIGHT, 0.2), Vector3(4, 4.3, 9))
	for ratio in [0.25, 1.0, 4.0]:
		var transported = Spatial.pose(source, dest, original, ratio)
		var restored = Spatial.pose(dest, source, transported, 1.0 / ratio)
		check(restored.origin.distance_to(original.origin) < 0.0001, "portal position " + str(ratio))
		check(restored.basis.is_equal_approx(original.basis), "portal orientation " + str(ratio))
		var v = Vector3(1, 2, 3)
		var result = Spatial.velocity(dest, source, Spatial.velocity(source, dest, v, ratio), 1.0 / ratio)
		check(v.distance_to(result) < 0.0001, "portal velocity " + str(ratio))
	var carried = Spatial.carry(source, dest, original)
	var local_before = source.affine_inverse() * original
	var local_after = dest.affine_inverse() * carried
	check(local_before.origin.distance_to(local_after.origin) < 0.0001, "carried position")
	check(local_before.basis.is_equal_approx(local_after.basis), "carried orientation")
	print("CORE_TEST_RESULT passed=", passed, " failed=", failed)
	print("SCOPE: transform unit tests only; no collisions or playthrough")
	quit(1 if failed else 0)
