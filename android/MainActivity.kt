package com.example.steersafeai

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException

// PDD NOTE: Replace 10.0.2.2 with your computer's actual local network IP (e.g. 192.168.1.XX) 
// if you are testing on a physical Android phone rather than the emulator.
private const val BASE_URL = "http://10.0.2.2:8000"

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = Color(0xFF6366F1),
                    background = Color(0xFF0A0E1A),
                    surface = Color(0xFF141A37)
                )
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    SteerSafeDashboard()
                }
            }
        }
    }
}

data class IncidentLog(val timestamp: String, val riskLevel: String, val message: String)

@Composable
fun SteerSafeDashboard() {
    val coroutineScope = rememberCoroutineScope()
    var predictedRisk by remember { mutableStateOf("SAFE") }
    var rawSensorText by remember { mutableStateOf("X: 0.00 | Y: 0.00 | Z: 9.81") }
    var smsAlertText by remember { mutableStateOf("No critical alerts triggered.") }
    var incidentLogs by remember { mutableStateOf(listOf<IncidentLog>()) }
    var isMonitoring by remember { mutableStateOf(false) }
    var selectedProfile by remember { mutableStateOf("Safe") }
    
    val client = remember { OkHttpClient() }

    // Color indicators based on risk
    val riskColor by animateColorAsState(
        targetValue = when (predictedRisk) {
            "SAFE" -> Color(0xFF10B981)
            "MODERATE RISK" -> Color(0xFFF59E0B)
            "HIGH RISK" -> Color(0xFFEF4444)
            else -> Color(0xFF10B981)
        }
    )

    // Helper functions for API calls
    fun fetchSimulation() {
        coroutineScope.launch(Dispatchers.IO) {
            val url = "$BASE_URL/simulate?behavior=$selectedProfile"
            val request = Request.Builder().url(url).build()
            try {
                client.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        val body = response.body?.string() ?: return@use
                        val json = JSONObject(body)
                        val risk = json.getString("predicted_risk").uppercase()
                        val samples = json.getJSONArray("samples")
                        
                        // Parse last sample
                        var sensorStr = "X: 0.00 | Y: 0.00 | Z: 9.81"
                        if (samples.length() > 0) {
                            val last = samples.getJSONObject(samples.length() - 1)
                            sensorStr = String.format(
                                "X: %.2f | Y: %.2f | Z: %.2f",
                                last.getDouble("ax"),
                                last.getDouble("ay"),
                                last.getDouble("az")
                            )
                        }

                        withContext(Dispatchers.Main) {
                            predictedRisk = risk
                            rawSensorText = sensorStr
                            if (risk == "HIGH RISK") {
                                smsAlertText = "[STEERSAFE SMS ALERT]\nWARNING: High Risk driving patterns detected via telemetry! profile: $selectedProfile"
                            }
                        }
                    }
                }
            } catch (e: IOException) {
                withContext(Dispatchers.Main) {
                    rawSensorText = "Connection Error to Server"
                }
            }
            
            // Refresh logs
            fetchLogs()
        }
    }

    fun fetchLogs() {
        coroutineScope.launch(Dispatchers.IO) {
            val url = "$BASE_URL/logs?limit=5"
            val request = Request.Builder().url(url).build()
            try {
                client.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        val body = response.body?.string() ?: return@use
                        val jsonArray = JSONArray(body)
                        val tempLogs = mutableListOf<IncidentLog>()
                        for (i in 0 until jsonArray.length()) {
                            val obj = jsonArray.getJSONObject(i)
                            tempLogs.add(
                                IncidentLog(
                                    timestamp = obj.getString("timestamp"),
                                    riskLevel = obj.getString("risk_level"),
                                    message = obj.getString("message")
                                )
                            )
                        }
                        withContext(Dispatchers.Main) {
                            incidentLogs = tempLogs
                        }
                    }
                }
            } catch (e: IOException) {
                // Ignore background errors
            }
        }
    }

    // Monitoring loop
    LaunchedEffect(isMonitoring) {
        if (isMonitoring) {
            while (isMonitoring) {
                fetchSimulation()
                delay(3000)
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // App Header
        Text(
            text = "🛡️ SteerSafe AI Mobile",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Color.White,
            modifier = Modifier.padding(vertical = 12.dp)
        )

        // Telemetry Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Select Driving Profile:", color = Color.LightGray, fontSize = 12.sp)
                
                // Segmented buttons simulation
                Row(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    val profiles = listOf("Safe", "Moderate Risk", "High Risk")
                    profiles.forEach { profile ->
                        Button(
                            onClick = { selectedProfile = profile },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (selectedProfile == profile) MaterialTheme.colorScheme.primary else Color.Gray.copy(alpha = 0.2f)
                            )
                        ) {
                            Text(profile, fontSize = 11.sp)
                        }
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Button(onClick = { fetchSimulation() }) {
                        Text("Predict Once")
                    }
                    Button(
                        onClick = { isMonitoring = !isMonitoring },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (isMonitoring) Color.Red else MaterialTheme.colorScheme.primary
                        )
                    ) {
                        Text(if (isMonitoring) "Stop Loop" else "Start 3s Loop")
                    }
                }
            }
        }

        // Risk Level Gauge box
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(110.dp)
                .padding(vertical = 8.dp)
                .background(riskColor.copy(alpha = 0.15f), shape = RoundedCornerShape(12.dp))
                .padding(16.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("DRIVING RISK STATE", color = Color.White.copy(alpha = 0.6f), fontSize = 10.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(4.dp))
                Text(predictedRisk, color = riskColor, fontSize = 26.sp, fontWeight = FontWeight.ExtraBold)
            }
        }

        // Live Sensors Box
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text("LIVE SENSOR TELEMETRY", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.Gray)
                Spacer(modifier = Modifier.height(6.dp))
                Text(rawSensorText, fontSize = 14.sp, color = Color.White)
            }
        }

        // Simulated SMS Alert Box
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            colors = CardDefaults.cardColors(
                containerColor = if (predictedRisk == "HIGH RISK") Color(0xFFEF4444).copy(alpha = 0.1f) else MaterialTheme.colorScheme.surface
            )
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text("SIMULATED SMS NOTIFICATIONS (GSM LINK)", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color.Gray)
                Spacer(modifier = Modifier.height(6.dp))
                Text(smsAlertText, fontSize = 13.sp, color = if (predictedRisk == "HIGH RISK") Color(0xFFFCA5A5) else Color.LightGray)
            }
        }

        // Incident Logs List
        Text(
            "Incident Logs",
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            color = Color.White,
            modifier = Modifier.align(Alignment.Start).padding(top = 10.dp, bottom = 4.dp)
        )
        LazyColumn(
            modifier = Modifier.fillMaxWidth().weight(1f),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            items(incidentLogs) { log ->
                val logColor = when (log.riskLevel.uppercase()) {
                    "SAFE" -> Color(0xFF10B981)
                    "MODERATE RISK" -> Color(0xFFF59E0B)
                    "HIGH RISK" -> Color(0xFFEF4444)
                    else -> Color.White
                }
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color.White.copy(alpha = 0.05f), shape = RoundedCornerShape(8.dp))
                        .padding(8.dp)
                ) {
                    Column {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(log.riskLevel, color = logColor, fontWeight = FontWeight.Bold, fontSize = 11.sp)
                            Text(log.timestamp, color = Color.Gray, fontSize = 10.sp)
                        }
                        Text(log.message, color = Color.LightGray, fontSize = 11.sp)
                    }
                }
            }
        }
    }
}
