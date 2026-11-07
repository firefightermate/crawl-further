using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Util
{
    /// <summary>
    /// Reads and writes the game's private fields by name. Most of Crawl's tuning lives in private serialized fields
    /// (m_healthMax, m_attacks...), so building content means setting them on cloned prefabs.
    /// <code>
    /// float hp = R.Get&lt;float&gt;(health, "m_healthMax");
    /// R.Set(player, "m_evolveCost", 2.5f);
    /// </code>
    /// Lookups are cached per type and name. A field that does not exist throws MissingFieldException.
    /// </summary>
    public static class R
    {
        // AccessTools.Field walks the type chain with a fresh closure on every call, and these run at runtime too
        // (spawn hooks, clip events, menus): remember each lookup
        static readonly Dictionary<Type, Dictionary<string, FieldInfo>> s_fields = new Dictionary<Type, Dictionary<string, FieldInfo>>();

        internal static FieldInfo F(Type t, string name)
        {
            Dictionary<string, FieldInfo> byName;
            if (!s_fields.TryGetValue(t, out byName)) s_fields[t] = byName = new Dictionary<string, FieldInfo>();
            FieldInfo f;
            if (byName.TryGetValue(name, out f)) return f;
            f = AccessTools.Field(t, name);
            if (f == null) throw new MissingFieldException(t.Name, name);
            byName[name] = f;
            return f;
        }

        /// <summary>The value of field <paramref name="field"/> (any visibility, declared on the object's type or a base type).</summary>
        public static T Get<T>(object o, string field) { return (T)F(o.GetType(), field).GetValue(o); }

        /// <summary>Set field <paramref name="field"/> (any visibility) of <paramref name="o"/>.</summary>
        public static void Set(object o, string field, object value) { F(o.GetType(), field).SetValue(o, value); }

        static readonly MethodInfo s_memberwiseClone = typeof(object).GetMethod("MemberwiseClone", BindingFlags.Instance | BindingFlags.NonPublic);

        /// <summary>A shallow copy of a plain data object (DamageEffectData, AttackData...), so a clone can be tuned without
        /// changing the vanilla original it shares the object with.</summary>
        public static T Clone<T>(T o) where T : class
        {
            return o == null ? null : (T)s_memberwiseClone.Invoke(o, null);
        }

        delegate bool Mapper(UnityEngine.Object from, out UnityEngine.Object to);

        /// <summary>
        /// Walk every serialized field of every component under <paramref name="root"/>, into nested [Serializable]
        /// classes, arrays and lists, and replace the UnityEngine.Object references that are keys of <paramref name="map"/>.
        /// Returns the number of replacements.
        /// </summary>
        internal static int RemapReferences(GameObject root, Dictionary<UnityEngine.Object, UnityEngine.Object> map)
        {
            return Walk(root, map.TryGetValue);
        }

        /// <summary>Visit every serialized UnityEngine.Object reference under <paramref name="root"/>; when the callback
        /// returns another non-null object, the reference is replaced with it.</summary>
        internal static int VisitReferences(GameObject root, Func<UnityEngine.Object, UnityEngine.Object> visit)
        {
            return Walk(root, (UnityEngine.Object k, out UnityEngine.Object v) => { v = visit(k); return v != null && v != k; });
        }

        static int Walk(GameObject root, Mapper map)
        {
            int n = 0;
            var visited = new HashSet<object>();
            foreach (var c in root.GetComponentsInChildren<Component>(true))
            {
                if (c == null || c is Transform) continue;
                n += RemapObject(c, map, visited, 0);
            }
            return n;
        }

        static int RemapObject(object o, Mapper map, HashSet<object> visited, int depth)
        {
            if (o == null || depth > 6) return 0;
            if (!(o is UnityEngine.Object) && !visited.Add(o)) return 0;
            int n = 0;
            var t = o.GetType();
            if (t.Assembly == typeof(GameObject).Assembly && !(o is MonoBehaviour)) return 0;   // engine components
            for (var tt = t; tt != null && tt != typeof(MonoBehaviour) && tt != typeof(object); tt = tt.BaseType)
            {
                foreach (var f in tt.GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.DeclaredOnly))
                {
                    if (f.IsNotSerialized || f.IsLiteral || f.IsInitOnly) continue;
                    var ft = f.FieldType;
                    object v;
                    try { v = f.GetValue(o); } catch { continue; }
                    if (v == null) continue;
                    UnityEngine.Object to;
                    if (typeof(UnityEngine.Object).IsAssignableFrom(ft))
                    {
                        if (map((UnityEngine.Object)v, out to)) { f.SetValue(o, to); n++; }
                    }
                    else if (ft.IsArray)
                    {
                        var arr = (Array)v;
                        var et = ft.GetElementType();
                        for (int i = 0; i < arr.Length; i++)
                        {
                            var e = arr.GetValue(i);
                            if (e == null) continue;
                            if (typeof(UnityEngine.Object).IsAssignableFrom(et))
                            {
                                if (map((UnityEngine.Object)e, out to)) { arr.SetValue(to, i); n++; }
                            }
                            else if (IsPlainSerializable(et)) n += RemapObject(e, map, visited, depth + 1);
                        }
                    }
                    else if (v is IList && ft.IsGenericType)
                    {
                        var list = (IList)v;
                        var et = ft.GetGenericArguments()[0];
                        for (int i = 0; i < list.Count; i++)
                        {
                            var e = list[i];
                            if (e == null) continue;
                            if (typeof(UnityEngine.Object).IsAssignableFrom(et))
                            {
                                if (map((UnityEngine.Object)e, out to)) { list[i] = to; n++; }
                            }
                            else if (IsPlainSerializable(et)) n += RemapObject(e, map, visited, depth + 1);
                        }
                    }
                    else if (IsPlainSerializable(ft))
                    {
                        n += RemapObject(v, map, visited, depth + 1);
                    }
                }
            }
            return n;
        }

        static bool IsPlainSerializable(Type t)
        {
            return t.IsClass && !t.IsPrimitive && t != typeof(string) && !typeof(UnityEngine.Object).IsAssignableFrom(t)
                   && t.IsDefined(typeof(SerializableAttribute), false);
        }
    }
}
