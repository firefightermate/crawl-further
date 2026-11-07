using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace CrawlFurther.Util
{
    /// <summary>
    /// A small JSON reader and writer. Unity 5.4's JsonUtility cannot see classes from BepInEx plugin assemblies (it
    /// silently drops nested arrays of them), so Core reads its own files. Objects are Dictionary&lt;string, object&gt;,
    /// arrays List&lt;object&gt;, numbers double.
    /// </summary>
    public static class MiniJson
    {
        /// <summary>Parse JSON text. Throws FormatException on text it cannot read.</summary>
        public static object Parse(string s)
        {
            int i = 0;
            return Value(s, ref i);
        }

        /// <summary>
        /// Write <paramref name="value"/> as JSON: dictionaries with string keys, lists and arrays, strings, numbers,
        /// bools and null. With <paramref name="indent"/>, each object member and array item goes on its own line,
        /// except arrays of numbers, which stay on one.
        /// </summary>
        public static string Write(object value, bool indent = true)
        {
            var sb = new StringBuilder();
            Write(sb, value, indent, 0);
            return sb.ToString();
        }

        static void Ws(string s, ref int i) { while (i < s.Length && char.IsWhiteSpace(s[i])) i++; }

        static bool At(string s, int i, string word) { return string.CompareOrdinal(s, i, word, 0, word.Length) == 0; }

        static object Value(string s, ref int i)
        {
            Ws(s, ref i);
            if (i >= s.Length) throw new FormatException("unexpected end of JSON");
            char c = s[i];
            if (c == '{') return Obj(s, ref i);
            if (c == '[') return Arr(s, ref i);
            if (c == '"') return Str(s, ref i);
            if (At(s, i, "true")) { i += 4; return true; }
            if (At(s, i, "false")) { i += 5; return false; }
            if (At(s, i, "null")) { i += 4; return null; }
            int st = i;
            while (i < s.Length && "+-0123456789.eE".IndexOf(s[i]) >= 0) i++;
            if (i == st) throw new FormatException("unexpected '" + c + "' at " + i);
            return double.Parse(s.Substring(st, i - st), CultureInfo.InvariantCulture);
        }

        static Dictionary<string, object> Obj(string s, ref int i)
        {
            var d = new Dictionary<string, object>();
            i++; Ws(s, ref i);
            if (s[i] == '}') { i++; return d; }
            while (true)
            {
                Ws(s, ref i);
                var k = Str(s, ref i);
                Ws(s, ref i); i++;   // ':'
                d[k] = Value(s, ref i);
                Ws(s, ref i);
                if (s[i] == ',') { i++; continue; }
                i++; return d;       // '}'
            }
        }

        static List<object> Arr(string s, ref int i)
        {
            var l = new List<object>();
            i++; Ws(s, ref i);
            if (s[i] == ']') { i++; return l; }
            while (true)
            {
                l.Add(Value(s, ref i));
                Ws(s, ref i);
                if (s[i] == ',') { i++; continue; }
                i++; return l;       // ']'
            }
        }

        static string Str(string s, ref int i)
        {
            var sb = new StringBuilder();
            i++;   // opening quote
            while (s[i] != '"')
            {
                if (s[i] == '\\')
                {
                    i++;
                    char e = s[i];
                    if (e == 'n') sb.Append('\n');
                    else if (e == 't') sb.Append('\t');
                    else if (e == 'r') sb.Append('\r');
                    else if (e == 'b') sb.Append('\b');
                    else if (e == 'f') sb.Append('\f');
                    else if (e == 'u') { sb.Append((char)Convert.ToInt32(s.Substring(i + 1, 4), 16)); i += 4; }
                    else sb.Append(e);
                }
                else sb.Append(s[i]);
                i++;
            }
            i++;
            return sb.ToString();
        }

        static void Write(StringBuilder sb, object v, bool indent, int depth)
        {
            if (v == null) { sb.Append("null"); return; }
            if (v is string || v is Enum || v is char) { Quote(sb, v.ToString()); return; }
            if (v is bool) { sb.Append((bool)v ? "true" : "false"); return; }
            if (v is float) { sb.Append(((float)v).ToString("R", CultureInfo.InvariantCulture)); return; }
            if (v is double) { sb.Append(((double)v).ToString("R", CultureInfo.InvariantCulture)); return; }
            if (v is IConvertible) { sb.Append(Convert.ToString(v, CultureInfo.InvariantCulture)); return; }
            var dict = v as IDictionary;
            if (dict != null)
            {
                sb.Append('{');
                bool first = true;
                foreach (DictionaryEntry kv in dict)
                {
                    if (!first) sb.Append(',');
                    first = false;
                    Break(sb, indent, depth + 1);
                    Quote(sb, Convert.ToString(kv.Key, CultureInfo.InvariantCulture));
                    sb.Append(indent ? ": " : ":");
                    Write(sb, kv.Value, indent, depth + 1);
                }
                if (!first) Break(sb, indent, depth);
                sb.Append('}');
                return;
            }
            var list = v as IEnumerable;
            if (list != null)
            {
                bool flat = true;
                foreach (var e in list) if (e is string || e is Enum || (e != null && !(e is IConvertible))) { flat = false; break; }
                sb.Append('[');
                bool first = true;
                foreach (var e in list)
                {
                    if (!first) sb.Append(flat && indent ? ", " : ",");
                    first = false;
                    if (!flat) Break(sb, indent, depth + 1);
                    Write(sb, e, indent, depth + 1);
                }
                if (!first && !flat) Break(sb, indent, depth);
                sb.Append(']');
                return;
            }
            Quote(sb, v.ToString());
        }

        static void Break(StringBuilder sb, bool indent, int depth)
        {
            if (!indent) return;
            sb.Append('\n');
            sb.Append(' ', depth * 2);
        }

        static void Quote(StringBuilder sb, string s)
        {
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < ' ') sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
        }
    }
}
