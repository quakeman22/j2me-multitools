package com.fish.capcom;

import android.os.Bundle;
import android.view.View;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;
import com.fish.capcom.editors.*;

public class GameToolsActivity extends AppCompatActivity {

    private static final String[] GAME_NAMES = {
        "AND1 Street Basketball",
        "Asphalt Urban GT",
        "R6: Lockdown",
        "Sexy Blocks",
        "无极 (The Promise)",
        "World of Warcraft"
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_game_tools);

        Spinner spinner = findViewById(R.id.gameSpinner);
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this,
            android.R.layout.simple_spinner_item, GAME_NAMES);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);

        spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) { swapFragment(pos); }
            @Override public void onNothingSelected(AdapterView<?> p) {}
        });

        if (savedInstanceState == null) swapFragment(0);
    }

    private void swapFragment(int pos) {
        Fragment f;
        switch (pos) {
            case 0:  f = new And1EditorFragment();       break;
            case 1:  f = new AsphaltEditorFragment();    break;
            case 2:  f = new R6EditorFragment();         break;
            case 3:  f = new SexyBlocksEditorFragment(); break;
            case 4:  f = new WujiEditorFragment();       break;
            default: f = new WowEditorFragment();        break;
        }
        getSupportFragmentManager().beginTransaction()
            .replace(R.id.fragmentContainer, f)
            .commit();
    }
}