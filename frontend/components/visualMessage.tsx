import { Card } from "@/components/ui/card";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer,
} from "recharts";

export default function VisualMessage({ schema }: { schema: any }) {
  const { chart_type, title, data, x_axis, y_axis } = schema;

//   // Convert y_axis values to numbers
//   const numericData = data.map((item: any) => ({
//     ...item,
//     [y_axis]: y_axis
//       ? Number((item[y_axis] || "0").toString().replace(/,/g, "").replace(" EGP", ""))
//       : 0,
//   }));



  return (
    <Card className="p-4 my-4 shadow-md rounded-2xl">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <div style={{ width: "100%", height: 400 ,border: "2px solid red"}}>
        <ResponsiveContainer width="100%" height="100%">
          <>
            {chart_type === "bar" && (
              <BarChart width={730} height={400} data={data}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="key" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Bar dataKey="value" fill="#8884d8" />
  
</BarChart>
            )}

            {chart_type === "line" && (
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey={x_axis} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey={y_axis} stroke="#3b82f6" />
              </LineChart>
            )}

            {chart_type === "pie" && (
              <PieChart>
                <Pie
                  data={data}
                  dataKey={y_axis || x_axis}
                  nameKey={x_axis}
                  cx="50%"
                  cy="50%"
                  outerRadius={120}
                >
                  {data.map((_: any, i: number) => (
                    <Cell key={i} fill={`hsl(${(i * 50) % 360}, 70%, 60%)`} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            )}
          </>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
