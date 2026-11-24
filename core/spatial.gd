extends RefCounted

static func pose(source: Transform3D, destination: Transform3D, original: Transform3D, ratio: float = 1.0) -> Transform3D:
	var local = source.affine_inverse() * original
	var turn = Basis(Vector3.UP, PI)
	return destination * Transform3D(turn * local.basis, turn * local.origin * ratio)

static func velocity(source: Transform3D, destination: Transform3D, original: Vector3, ratio: float = 1.0) -> Vector3:
	return destination.basis * Basis(Vector3.UP, PI) * source.basis.inverse() * original * ratio

static func carry(previous: Transform3D, current: Transform3D, passenger: Transform3D) -> Transform3D:
	return current * previous.affine_inverse() * passenger
