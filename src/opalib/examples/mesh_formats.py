import opalib.format as F

F.format("Point", F.struct([
    {"id": F.ID},
    {"v3": F.V3},
    {"ptype": F.Byte}
]))
F.new("PointSight", F.map(F.Ref.Points, F.Double))
F.format("Surface", F.union(
    F.list(F.Ref.Points),
    F.struct([
        {"id": F.ID},
        {"c_conns": F.map(F.Ref.Points, F.Ref.CConns)}
    ])
))

F.new("Barrier", F.union(F.Surface, [
    {"is_barrier": F.konst(True, F.Bool, False)}
]))

F.format("CConnection", F.struct([
    {"action": F.Int},
    {"fromID": F.Int},
    {"toID": F.Int},
    {"i1": F.Int},
    {"i2": F.Int},
    {"j1": F.Int},
	{"j2": F.Int},
	{"t1": F.Double},
	{"t2": F.Double},
	{"u1": F.Double},
	{"u2": F.Double}
]))

F.format('Connection', F.struct([
	{"type": F.String},
	{"bidirectional": F.Bool},
	{"at": F.map(F.Ref.Points, F.konst(True, F.Bool, False))},
	{"to": F.map(F.Ref.Points, F.konst(True, F.Bool, False))}
])); print(F)
F.format('Mesh', F.struct([
	{"Name": F.String},
	{"Visible": F.Bool},
	{"points": F.list(F.Point, 'Points')},
	{"c_conns": F.GE_VER(2, F.list(F.CConnection, 'CConns'), None)},
	{"surfaces": F.list(F.Surface, 'Surfaces')},
	{"barriers": F.GE_VER(3, F.list(F.Barrier, 'Barriers'), None)},
	{"connections": F.list(F.Connection)}
]))

F.new('MeshSave', F.struct([
	{"version": F.save(
		'version',
		F.konst(F._VERSION, F.Int, True)
	)},
	{"mesh": F.Mesh}
]))
F.new('MeshReq', F.struct([
	{"version": F.save(
		'version',
		F.konst(F._VERSION, F.Int, True)
	)},
	{"params": F.map(F.String, F.Any)},
	{"mesh": F.Mesh}
]))