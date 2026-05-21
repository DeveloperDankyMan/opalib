local e = _G

local Ref_MT = {};
local F = {
	_VERSION = 3;
	ID = {};
	V3 = {};
	Byte = {};
	Double = {};
	Int = {};
	Int64 = {};
	String = {};
	Any = {};
	Bool = {};
	Ref = {};
}
setmetatable(F.Ref, Ref_MT);

function F.map(k_format, v_format)
	return {
		type = 'map';
		k_format = k_format;
		v_format = v_format;
	}
end

function F.list(v_format, key)
	return {
		type = 'list';
		v_format = v_format;
		key = key;
	}
end

function F.array(len, v_format, key)
	return {
		type = 'array';
		v_format = v_format;
		len = len;
		key = key;
	}
end

function F.union(...)
	return {
		type = 'union';
		...
	}
end

function F.struct(fields)
	return {
		type = 'struct';
		fields = fields
	}
end

function F.konst(value, v_format, is_serialized)
	return {
		type = 'konst';
		value = value;
		v_format = v_format;
		is_serialized = is_serialized;
	}
end

function F.save(name, v_format)
	return {
		type = 'save';
		name = name;
		v_format = v_format;
	}
end

function F.compat(func)
	return {
		type = 'compat';
		func = func;
	}
end

function F.enable_if(cond, v_format)
	return {
		type = 'enable_if';
		cond = cond;
		v_format = v_format;
	}
end

function F.format(name, t)
	t.name = name
	e[name].format = t
end

function F.new(name, t)
	t.name = name
	F[name] = t
end

function F.GE_VER(ver, on_true, on_false)
	return F.compat(function(ctx)
		if ctx.version >= ver then
			return on_true
		else
			return on_false
		end
	end)
end

function Ref_MT:__index(name)
	local v = {
		type = 'ref';
		of = name;
	}
	self[name] = v
	return v
end

function F.String:load(data, i)
	return e.util.read_s(data, i)
end
function F.Bool:load(data, i)
	local b = data:sub(i, i)
	i = i + 1
	return b == string.char(1), i
end
function F.V3:load(data, i)
	return e.util.read_v(data, i)
end

function F.Byte:load(data, i)
	return data:sub(i, i):byte(), i + 1
end

function F.Double:load(data, i)
	return e.util.read_d(data, i)
end

function F.Int:load(data, i)
	return e.util.read_i(data, i)
end

function F.Int64:load(data, i)
	return e.util.read_i64(data, i)
end

function F.Any:load(data, i)
	return e.util.read_a(data, i)
end

function F.String:save(data)
	return e.util.a(data, e.util.s2b(self))
end
function F.Bool:save(data)
	return e.util.a(data, self
		and string.char(1)
		or string.char(0))
end
function F.V3:save(data)
	return e.util.a(data, e.util.v2b(self))
end

function F.Byte:save(data)
	return e.util.a(data, string.char(self))
end

function F.Double:save(data)
	return e.util.a(data, e.util.d2b(self))
end

function F.Int:save(data)
	return e.util.a(data, e.util.i2b(self))
end

function F.Int64:save(data)
	return e.util.a(data, e.util.i642b(self))
end

function F.Any:save(data)
	return e.util.a(data, e.util.a2b(self))
end

F.new('Challenge', F.struct{
	{signature = F.array(16, F.Byte)};
	{issued = F.Int64};
	{difficulty = F.Byte};
	{K00 = F.Int};
	{K01 = F.Int};
	{K10 = F.Int};
	{K11 = F.Int};
})

F.new('Solution', F.struct{
	{x = F.Int};
	{y = F.Int};
})

return F